# Repository Guidelines

`cx-studio-tk` 是一个面向影视后期制作的 Python 工具集，采用 uv workspace 组织的 monorepo。
包含 `cx-studio`（基础设施）、`cx-wealthy`（Rich UI 组件）、`cxalio-studio-tools`（CLI 工具集）三个主力包；已停止维护的旧包（`cx-wealth`、`media_killer_legacy`）存档于 `archived/`，仅作参考，不参与构建、不再维护。

## 权威标记

本文件与 `docs/` 下规范文档中的规则类内容分三级：

- **[MUST]** / **[MUST NOT]**——硬约束，违反即缺陷
- **[SHOULD]** / **[SHOULD NOT]**——推荐惯例，偏离需说明理由
- **[MAY]**——建议性做法，可选

未标等级的陈述为事实描述或设计哲学，非行为约束。

## 文档地图

- 根 `AGENTS.md`（本文件）：全仓库规范入口，全局基线，优先于其他规范文档
- 根 `CONTEXT.md`：仓库统一领域文档，按 `## Domain:` 分区（定位/架构/约定/术语）——处理 `packages/` 下某 workspace 的内容时 **[MUST]** 阅读对应分区
- `docs/adr/`：设计决策记录，单一编号序列；**[MUST]** 阅读适用范围覆盖目标 workspace 的 ADR，索引见 `docs/adr/README.md`
- `docs/agents/`：工作流文档（issue tracker、triage 标签、领域文档消费规则、i18n 工作流）
- 领域术语或设计决策发生变化时，**[MUST]** 优先更新 `CONTEXT.md` 与 `docs/adr/`，再继续代码工作

## 命令与环境

所有命令在 workspace 根目录执行。

### 依赖

```bash
uv sync                   # 安装/同步所有依赖
uv sync --group dev       # 安装 dev 依赖（含 black）
```

### 运行工具

```bash
uv run mediascout --help
uv run mediakiller --help
uv run ffpretty --help
uv run jpegger --help
uv run hostskeeper --help
uv run cxnote --help
```

### 格式化

```bash
uv run black .            # 项目中唯一格式化工具，提交前运行
```

### 构建

```bash
uv build                  # 构建所有包
```

### 测试

- ⚠️ 项目当前**没有**测试基础设施。无测试目录、无测试依赖、无 CI。
- **[MUST NOT]** 尝试运行测试命令——它们不存在。

## 项目结构

|Directory|Purpose|
|---|---|
|`packages/cx-studio/cx_studio/`|基础设施库——值对象、FFmpeg、文件系统、IO、系统抽象|
|`packages/cxalio-studio-tools/`|CLI 工具集——应用框架 + 6 个工具（media_scout: Chain of Responsibility / media_killer: Async Mission Pipeline / jpegger: ImageFilterChain / ffpretty: FFmpeg 封装 / hosts_keeper: Plugin-based 管理 / cxnote: 域组织便签）|
|`packages/cxalio-studio-tools/cx_tools/app/`|应用生命周期框架（IApplication + IAppEnvironment）|
|`archived/cx-wealth/cx_wealth/`|Rich UI 扩展——标签、详情、帮助系统 DSL（已停止维护，仅存档）|
|`temp/`|临时/调试文件（gitignored，勿在此编写正式代码）|
|`archived/`|已停止维护的旧代码存档（`cx-wealth`、`media_killer_legacy`），不参与构建，不修改|

## 架构

### 依赖链

- `cxalio-studio-tools` 同时依赖 `cx-studio` 与 `cx-wealthy`
- `cx-studio` 与 `cx-wealthy` **平级**——互不依赖（cx-wealthy 仅依赖 `rich`，见 ADR-0010）

### CLI 应用通用生命周期（所有 6 个工具一致）

1. `[project.scripts]` 入口 → `module:run()` 函数
2. `Application.__enter__()` → `IAppEnvironment` 初始化（Rich console、SIGINT、debug 门控）
3. `Application.run(appenv)` → 解析参数 → 执行业务逻辑
4. `Application.__exit__()` → 清理

### 项目特有模式

领域文档为仓库级单套，不按 workspace 分散：

- [CONTEXT.md](CONTEXT.md)——统一领域文档（按 `## Domain:` 分区，处理对应 workspace 时阅读相应分区）
- [docs/adr/](docs/adr/)——设计决策记录（单一编号序列，每篇标注领域与适用范围；索引见 `docs/adr/README.md`）

消费规则见 `docs/agents/domain.md`。

## 开发规则

**目标平台**：Windows / macOS / Linux。**[MUST]** 涉及路径操作时使用 `pathlib.Path`，避免字符串拼接；涉及文件编码时**[MUST]** 显式指定 `encoding="utf-8"`。

### 流程

#### 执行规则

- **[MUST]** 处理 `packages/` 下某个 workspace 的内容时，先阅读根 `CONTEXT.md` 的对应 `## Domain:` 分区与 `docs/adr/` 中适用范围覆盖该 workspace 的 ADR。本文件是全局基线，领域文档承载各 workspace 独有的架构、约定与决策记录（按 Domain 分区与适用范围标注组织）
- **[MUST]** 修改代码后运行 `uv run black .`
- **[MUST]** 为新公共函数/类添加 docstring

#### 先问再做

以下动作**[MUST]** 先征得用户同意：

- 添加新依赖（`uv add`）或修改 `pyproject.toml`
- 修改版本号（`__init__.py` 中的 `__version__` 及对应 `pyproject.toml`）
- 修改分支策略相关配置（branch protection / CI workflow / git hooks）

#### 禁止项

- **[MUST NOT]** 未经允许直接推送 `main` 分支（发布需用户确认）
- **[MUST NOT]** 在生产环境运行未经测试的 CLI 工具
- **[MUST NOT]** 在 Box→Dataclass 桥接场景之外使用 `# type: ignore`（详见下方「数据模型选择」）
- **[MUST NOT]** 将测试、调研等临时产物直接散落在项目根目录或 `packages/` 下——一律放入 `temp/`
- **[MUST NOT]** 删除 `.env` 文件或任何非临时的配置文件（如 `pyproject.toml`、`.github/`、CI 配置）

### 设计规范

#### 命名约定

- 类：PascalCase；函数/方法：snake_case
- 供他人 import 的依赖模块/包使用库名缩写前缀（如 `cx_`、`wealth_`）以避免与使用者的模块重名；`cx_tools` 应用框架同样遵循此惯例。纯 CLI 入口工具（media_scout、media_killer 等）不受此限。
- ABC/接口：`I` 前缀（IApplication、IAppEnvironment、ITimeRange、IPathValidator）
- 私有类/函数：`_` 前缀（_Node、_Group）

#### 导入规则

- 每个子包通过 `__init__.py` star-import 汇聚所有公开符号
- 通用包使用别名导入，将符号来源带到调用点：
  - `r` → `cx_wealthy.rich_types`（Rich 类型统一出口）
  - `tt` → `cx_studio.text`（文本工具）
- 依赖 `cx-wealthy` 的包**优先**通过 `cx_wealthy.rich_types` 引用常用 Rich 类型；非组件类功能（如 `rich.traceback.install`）与低频类型可直接 import rich；`cx_studio` 本身不依赖 `cx-wealthy`，可直接使用 Rich 原生导入

#### 数据模型选择

|场景|使用|不使用|
|---|---|---|
|有固定 schema、接口契约|`@dataclass(frozen=True)`|`dict` 或 `Box`|
|无固定 schema、运行时结构不定|`python-box`（`.attr` 多层访问）|裸 `dict`|
|序列化边界（`tomllib.load()` 返回值）|裸 `dict` → 立即桥接为 Box/Dataclass|保留 dict 在业务层传递|
|Box→Dataclass 桥接|`# type: ignore` **可接受**|—|

**硬约束**：`# type: ignore` **仅允许**在 Box→Dataclass 桥接边界使用。项目其他位置禁止无理由使用。

#### 展示协议

- `__rich_label__()` → 紧凑标签（yield Renderable 片段，用于列表行标题）
- `__rich_detail__()` → 详情面板（yield `(key, value)` 二元组，渲染为两列表格）
- 两者可共存；核心领域类型应同时实现。可通过 `yield from super().__rich_label__()` 复用父类标签。

#### asyncio 事件命名

- **事件名称必须通过常量定义**，禁止直接使用字符串字面量调 `emit()`/`on()`。常量在事件发射组件的模块文件顶级中定义。
- **事件名使用 `-ED` 形式**（如 `STARTED`、`FINISHED`、`CANCELED`、`FILE_LOGGED`），表明事件是对**已发生的状态跃迁**的通知，而非对将来动作的请求或描述过程（不应使用 `-ING`、无后缀动词原形等形式）。
- **事件常量通常不在 `__init__.py` 中包级导出**，避免命名冲突（不同组件可能定义同名事件，如 `FILE_LOGGED` 在 executor 级别和 HQ 级别含义不同）。外部消费者从定义常量的模块直接导入：
  ```python
  from .media.mission_hq import MISSION_STARTED
  # 而非 from .media import MISSION_STARTED
  ```
- 同一组件内部使用常量调用 `emit()`/`on()` 也遵循此规则——虽非强制，但推荐以保持可 grep 性和一致性。

### 代码风格

#### 类型标注

- 全量 type hints；Python 3.10+ union syntax（`X | Y`）；`@override`（PEP 698，3.12+）
- 从 `collections.abc` 导入集合类型，不使用 `typing` 中已废弃的同名等价物

#### 文档与注释

- **docstring 语言**：统一简体中文。docstring 面向 IDE 悬停与代码阅读，属代码注释，不参与 gettext 翻译
- **docstring 风格**：Google 风格——首段说明用途；参数、返回值、异常分别用 `Args:`、`Returns:`、`Raises:` 段落描述；类型信息写全，与签名一致
- **覆盖要求**：公开类、函数、方法必须有 docstring。dunder 方法与 `_` 私有成员不逐条撰写；若成员含非显然语义（如与字面量比较的特判、跨类型转换规则），在类级 docstring 中集中说明
- **独立呈现**：docstring 禁止引用 ADR 编号、`docs/` 路径、issue 编号等仓库外部文档——代码文档自足，IDE 悬停读者不应被要求跳转其他文件才能理解；决策背景确有必要时，用一句话陈述语义本身，不写「见 ADR-00XX」。该约束单向：文档（CONTEXT/ADR）可引用代码符号，代码不反向引用文档
- 行内注释只解释代码表达不了的决策理由
- 修改代码后自底向上检查注释是否仍匹配（行内→方法→类→模块）

## 版本管理

### 概念：两个版本号

- `__version__`（包的真实版本）：每个真正的包在 `__init__.py` 顶层定义 `__version__: str`（PEP 396）。它是该包实际版本的语义载体；CLI 工具 `appenv.py` 从所在包引入并展示（`from . import __version__`）。
- pyproject `version`（发布单元版本）：机制性版本，用于触发更新、解析依赖。发布单元内容发生变化时它必须迭代——否则依赖机制认为该版本没有变化，不会触发更新。
- 正常情况下两者数值同步；区别在用途与地位，不在数值。

### 迭代逻辑（因果链，重读时以此为准）

- 迭代的**旧值来源永远是 pyproject**，而不是 `__version__`。原因：pyproject 是实际发布过的版本的可靠记录（依赖解析、分发都以它为准），即使 `__version__` 因历史原因与它不一致，pyproject 仍是事实来源——从它出发迭代不会建立在错误基础上。
- 迭代出的**新版本号写入 `__version__`**：真实版本的地位不变，新版本号落在它上面。
- 因为 `__version__` 更新了，**pyproject 随之同步**为新版本号。
- 即：读 pyproj 旧值 → 基于该值判断新版本号 → 写 `__version__` → pyproj 同步。pyproject 是起点（旧值来源），`__version__` 是落点（真实版本），同时 pyproject 也是跟随者。

### 迭代流程（所有包统一）

- 读取 pyproject 当前版本 → 参考幅度策略判断新版本号 → 新版本号写入变更包的 `__version__` → pyproject 同步。
- 时机：修改后不立即迭代；agent 不直接修改版本号，应向用户建议（含建议的新版本号），**由用户确认触发、拍板最终版本号**。

### 版本号幅度策略（判断提示）

格式：`major.minor.patch[.hotfix]`。以下映射是迭代版本号时的**初步判断提示**；实际迭代由用户确认触发，最终版本号由用户拍板。

|档位|步进|判断依据|
|---|---|---|
|hotfix|第四段 +1|笔误、格式修正等不影响任何功能的修改|
|patch|patch 位 +1|修复、重构已有功能；bug、算法修复|
|minor|minor 位 +1|新增功能、组件、能力、新 tool；删除此类内容（单点能力面变化）|
|major|major 位 +1|大幅架构调整、大量功能重构、里程碑式进化；API 级变更、明显破坏兼容性的变更|

补充约定：

- **hotfix 段在本项目表示最低档变更**，非标准 SemVer 的"发布后紧急修复"语义
- 一次迭代含多档变更时，按最高档位判断
- hotfix 段存在时向更高位步进，低段位清零（1.0.0.3 → patch 1.0.1 / minor 1.1.0）
- 纯文档、注释、i18n 译文修改：hotfix 档
- 删除功能/组件属于单点能力面变化 → minor；**删除公开 API 或改变接口契约、明显破坏兼容性 → major**（即使单点）

### 单包发布单元（cx-studio / cx-wealthy）

- 发布单元即包本身。包内容变更 → 按迭代流程执行，该包 `__version__` 与 pyproject 同步更新。

### cxalio-studio-tools 多包发布单元

- 6 个工具与 cx_tools **没有自己的 pyproject，共享 cxalio-studio-tools 的 pyproject**——它是这些包共同的发布版本。
- 某包（工具或 cx_tools）内容变更 → 从共享 pyproject 读当前发布版本 → 判断新版本号 → 写入该包 `__version__` → pyproject 同步。
- **同一迭代批次中多个变更包共享同一个新版本号**：各包从同一旧值判断一次，分别写入各自 `__version__`，pyproject 只同步一次（如 ffpretty 与 media_scout 同批变更都得到 2.0）。
- **未变更包的 `__version__` 不动**。因此每个包 `__version__` 的数值 = 该包最后一次变更时的发布版本快照：各包之间、以及与最终 pyproject 之间数值都允许不同——这是设计而非失控。
- 推论（快照语义的自然结果）：某包在其它包多次迭代之后再变更时，会直接从当前 pyproject 版本继续迭代（如停在 1.1 的包在发布版本到 2.0 后再次变更 → 2.1），版本号"跳级"是正常的。
- cx_tools 与其它工具同一逻辑，无专项同步。

### CHANGELOG 政策：不设 CHANGELOG 文档

- 各包**不再维护 `CHANGELOG.md`**（历史文件已移除；内容留存于 git 历史与 commit message）。
- **commit message 即变更记录**：它是该次变更的唯一叙述，须**独立、完备、简洁、清晰**——脱离 diff 即可读懂「改了什么、为什么」。
- commit message 记述变更的意图与影响边界，**不赘述实现细节**：具体内容由 diff 提供，正文不重复代码、不复述 diff 已呈现的事实。
- 迭代发布时无 CHANGELOG 动作；版本号仍按上文流程由用户确认触发。

## Git 工作流

- **main** — 发布分支，只接受从 `dev` 的 `--no-ff` merge
- **dev** — 开发分支，所有功能最终合入
- **临时分支** — 从 `dev` 迁出，完整实现后 merge 回 `dev`；一般不 push 到远程
- 分支命名：`feat/<描述>`、`fix/<描述>`、`chore/<描述>`
- Commit 格式：`type(scope): 描述`（type: feat/fix/docs/chore/refactor）
- **[MUST NOT]** 未经允许推送 `main`

## 国际化（i18n）

项目使用 **gettext + Babel** 做 i18n，每包自持翻译文件。

### 源语言政策

**本项目以简体中文（zh_CN）为标准语言，代码中所有 `_()` 调用使用中文 msgid。**
其他语言的翻译通过 `.po` 文件的 `msgstr` 字段提供。

**注意**：由于源语言是简体中文，**不需要也不应当创建 `zh_CN` 的 `.po`/`.mo` 文件**。原因是 gettext 回退行为：找不到 `.mo` 时直接返回 msgid（即中文原文）；而空 msgstr 的 `.mo` 反而会覆盖 msgid 返回空字符串。`zh_CN` 翻译文件的存在只会引入风险，不应提交到仓库。

### 入口导入

|所在包|导入路径|用途|
|---|---|---|
|cx-studio|`from cx_studio.i18n import _, _ng`|基础设施字符串|
|cx_tools（框架）|`from cx_tools.i18n import _, _ng`|框架自身字符串|
|media_scout|`from media_scout.i18n import _, _ng`|media_scout 工具字符串|
|media_killer|`from media_killer.i18n import _, _ng`|media_killer 工具字符串|
|ffpretty|`from ffpretty.i18n import _, _ng`|ffpretty 工具字符串|
|jpegger|`from jpegger.i18n import _, _ng`|jpegger 工具字符串|
|hosts_keeper|`from hosts_keeper.i18n import _, _ng`|hosts_keeper 工具字符串|
|cx_note|`from cx_note.i18n import _, _ng`|cxnote 工具字符串|

工具模块**必须**从所在工具自己的 `i18n` 模块导入——`media_killer` 中的模块从 `media_killer.i18n` 导入，不交叉导入 `cx_tools.i18n`。`cx_tools` 框架自身的模块仍从 `cx_tools.i18n` 导入。

> `cx-wealthy` 不参与 gettext 翻译——UI 组件输出为框架固定文本，由使用方控制，详见根 [CONTEXT.md](CONTEXT.md) 的 cx-wealthy Domain 分区。

> 每个工具独立 domain 和翻译文件：domain 分别为 `cx-tools`、`media-scout`、`media-killer`、`ffpretty`、`jpegger`、`hosts-keeper`、`cx-note`。各工具自持 `i18n/locales/`，互不交叉。

### 环境变量与 locale 检测

`gettext` 按 `LANGUAGE` → `LC_ALL` → `LC_MESSAGES` → `LANG` 的顺序选择 locale。

**注意**：终端环境经常设置 `LC_ALL=C.UTF-8`，它会覆盖 `LANG` 导致 locale 检测回退到 `C`，使翻译 `.mo` 不被加载（此时 `_()` 直接返回中文 msgid）。这不是 bug，而是 POSIX 标准行为。

如需测试其他语言的翻译，清除 `LC_ALL` 再设 `LANG`：

```bash
LC_ALL= LANG=en_US.UTF-8 hostskeeper --help
```

### 标记约定

- **`_("中文源字符串")`** —— 仅包裹固定的用户面向文本
- **变量在 `_()` 外面**：`_("已添加 {count} 个文件。").format(count=n)`
- **Rich markup 在外面**：`f"[cx.error]{_('操作失败')}[/]"`
- **复数**：`_ng("找到 {n} 个结果", "找到 {n} 个结果", n).format(n=n)`（中文单复数相同，翻译时在目标语言区分）
- **不翻译**：变量值、文件路径、URL、FFmpeg 输出、异常栈追踪、命令行参数名、debug-only 日志

### 提取与编译工作流

添加新字符串后的 pybabel 提取/更新/编译命令、`.mo` 提交要求与验证方法：**[MUST]** 阅读 [docs/agents/i18n.md](docs/agents/i18n.md)。

## Agent skills

### Issue tracker

issue 与 spec 以本地 markdown 跟踪：`.scratch/<feature-slug>/` 一特性一目录，spec 为 `spec.md`，票为 `issues/NN-<slug>.md`，文件顶部 `Status:` 行记录状态。详见 `docs/agents/issue-tracker.md`。

### Triage labels

状态词汇 = 五个 triage 角色（`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`）+ 落地标签 `implemented`；实现完成后置 `implemented` 收尾，`wontfix` 自身即终态。详见 `docs/agents/triage-labels.md`。

### Domain docs

领域文档为仓库级单套：根 `CONTEXT.md`（按 Domain 分区，处理对应 workspace 时阅读相应分区）+ 根 `docs/adr/`（单一编号序列，每篇标注领域与适用范围；索引见 `docs/adr/README.md`）。详见 `docs/agents/domain.md`。
