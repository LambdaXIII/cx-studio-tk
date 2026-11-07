# Design

## Context

现行输入处理在 `application.py` 的 `run()` 中逐条分类：`_resolve_preset()` 把每条输入二选一为预设或源，源再交 `SourceExpander` 展开。两个结构性问题：① `_resolve_preset` 的无扩展名分支对存在的目录返回原路径，目录被当作预设加载而炸出 `PermissionError`（触发 bug）；② `SourceExpander` 的后缀过滤集合来自已加载预设，形成「展开依赖提炼结果」的倒挂依赖。相关组件均为不依赖 appenv 的通用功能组件（`components/expander.py`、`components/preset/loader.py`）；InspectorChain 由 application 组装后注入。

## Goals / Non-Goals

**Goals:**

- 输入侧拆为两个互不依赖的环节，衔接仅为 `[Path]`：输入解析（字符串 → 存在、可读、绝对、去重、排序的路径集合）与资源提炼（路径集合 → 预设与源 → missions）。
- 修复目录输入误判为预设的 bug。
- 消除后缀过滤对预设的倒挂依赖。
- 输入解析与资源提炼各自可独立验证（喂字符串集合得路径集合；喂路径集合得预设与源）。

**Non-Goals:**

- 不改动执行/调度/脚本生成/pretend 行为与 `-g` 示例导出。
- 不改动 `PresetLoader`、`MissionMaker`、`ScriptMaker`、`MissionStore` 的契约。
- 不改动 media_scout 的 Inspector 体系。
- 不引入测试基础设施（仓库当前无测试设施，验证走冒烟脚本，见 tasks）。

## Decisions

**D1 · 环节一落地为新组件 `InputResolver`（`components/input_resolver.py`，替换 `expander.py`）**

现 `SourceExpander` 重构而来：类名 `InputResolver`，入口 `resolve(*inputs: str) -> list[Path]`——返回清单而非 Generator，因为「查重 + 排序」是环节一的输出契约，流式语义装不下。移除 `suffixes` 构造参数——环节一不感知源后缀与预设，仅有的格式感知是缺失输入的 `.toml` 补全与项目文件类型识别；项目文件扩展名集合随 `expander.py` 移入，并按裁定扩充 `.ps1`/`.sh`（与 FileListInspector 及 help 承诺对齐）。六个 Inspector 的组装代码从 application 移入 resolver 模块内部自持（media_scout 侧自身的组装不动——「只动一处」指 media_killer 内部）。InspectorChain 携带跨调用的去重状态，MUST 在每次 `resolve()` 调用内以 `with` 使用，并关闭其内部去重（`allow_duplicated=True`）：查重统一由集合层按绝对路径执行，项目文件产出的原始相对路径不得成为去重键，否则不同项目文件的同名相对引用会互相抑制。组件分层不变：不依赖 appenv 的通用功能组件。

**D2 · 补全规则收窄，原「无扩展名文件按预设原样加载」弃用**

环节一内：路径不存在且无扩展名时，追加 `.toml` 后缀判定（`with_suffix` 在无扩展名前提下即等价追加），命中且命中者为文件才采用。现行 `_resolve_preset` 的另一分支「无扩展名文件本体存在 → 按预设原样加载」**弃用**：新模型下存在的无扩展名文件进入路径集合，在环节二按既有后缀过滤体系排除（用户已裁定不额外处理）。迁移说明：无扩展名的旧预设文件须删除或改名 `.toml`——补全仅在裸路径不存在时生效，裸文件存在时同名 `.toml` 不会被读取。`-g` 导出恒带 `.toml` 后缀，常规流程不受影响。

**D3 · 环节二落在 application，提炼抽为纯函数**

`run()` 的步骤 4-6 重排为：① `paths = InputResolver().resolve(*ctx.inputs)`；② 提炼——抽为模块级纯函数 `_extract_presets_and_sources(paths) -> tuple[list[Preset], list[Path]]`（环节二因此获得「喂 `[Path]` 得预设与源」的可调用边界，Goals 的「各自可独立验证」成立；`run()` 只做呈现）：按扩展名分出 `.toml` 交 `PresetLoader`（失败经 `SafeError` 包装，沿用现模板「加载预设文件 {path} 失败: {err}」，`path` 展示集合中的绝对路径），全部提炼完成后合并 `source_suffixes`，其余路径按后缀过滤（大小写不敏感）为源；③ 任务组装（`MissionMaker` 调用、continue 叠加、mission 级排序去重均不变）。代价说明：路径集合是唯一衔接，预设加载排在全量展开之后——坏预设须等整棵目录树走完才报错，快速失败性较旧流程有损失；这是环节解耦的直接代价，接受。

**D4 · 旧承重行为的去向登记（收割清单）**

| 现行行为 | 去向 |
|---|---|
| 目录输入报 `加载预设文件失败: [Errno 13]` | 消灭——目录在环节一展开（本变更目的） |
| 源不存在报「源文件不存在: {path}」（application 步骤 6 的事后检查） | 移除——环节一已保证存在，检查点前移；报错形态由环节一的「不存在/不可读报错」承接 |
| 「预设文件不存在：{path}」（PresetLoader FileNotFoundError） | 主流程不再触发（环节一保证存在）；消息保留在 loader 自身契约中，不删 |
| 项目文件引用缺失媒体路径静默跳过 | 保留（规格已声明为合法排除） |
| 展开时按后缀过滤 | 移至环节二，语义不变 |
| 相对输入基于 CWD 解析、项目文件内相对路径基于项目文件位置解析 | 保留，均在环节一 |
| 逐条输入的 whisper（「配置文件路径」/「媒体来源路径」） | 预设侧保留（面板 + 路径 whisper）；「媒体来源路径」逐条 whisper 删除——来源来自展开，逐条提示语义已失真，汇总句「已添加 N 个配置文件和 M 个来源路径」承担告知 |
| `--sort x`「保持输入顺序」 | 语义变为「保持路径集合顺序」（环节一排序是已裁定行为）；app_help 的对应描述一并修正 |
| 目录 + 同名 `.toml` 的隐式配对（旧 `with_suffix` 判定先于存在判定，目录会让位给同名 toml） | 消灭——目录优先展开，`.toml` 不再自动配对（补全收窄的自然结果） |
| 汇总句计数口径 | 原「来源路径」计原始输入条目数；改为提炼后的源文件数，文案同步改为「已添加 N 个配置文件和 M 个源文件」 |

**D5 · 可读性尽力检测，检查范围限于原始输入与提取的预设**

检测手段为 `os.access(path, os.R_OK)`，对象为原始输入路径与环节二加载的预设文件；目录展开产物与项目文件引用不逐个探测（展开产物必然存在；媒体库规模下逐个探测代价高，且 Windows 对 ACL 拒读的检测本就不完全可靠）。漏检时不静默：预设文件在环节二报错中止并指明路径；源文件的不可读在执行期以该任务失败呈现（MissionHQ 单项 FAILED），均带路径可循——spec 的「尽力检测 + 漏检不静默」以此条为准。

**D6 · 查重键为绝对路径，排序为平台路径序**

路径集合 `sorted(set(...))`（Path 比较即平台路径序，确定性满足）。Windows 上 `Path` 的相等与哈希大小写不敏感，查重按大小写折叠——平台语义，接受并登记。排序使任务顺序不随 rglob/输入顺序漂移；执行顺序语义由 mission 级排序去重继续承接（`--sort x` 的语义变化见 D4）。

## Risks / Trade-offs

- **目录内杂散 `.toml` 会成为预设**（规格已裁定）：媒体库目录混有无关 toml 时，提炼会因 lint 失败而中止——新失败面。用户处置方式为移除该 toml；不做「仅顶层提取」之类特例（特例破坏环节解耦）。
- **全量展开的内存面**：环节一不再边展开边过滤，超大目录树全量入清单后由环节二过滤。现状 rglob 本就全遍历，差量仅为清单常驻内存，可接受。
- **报告输出面变化**：逐条「媒体来源路径」whisper 删除（D4）。属 debug-only 输出，无契约影响。
