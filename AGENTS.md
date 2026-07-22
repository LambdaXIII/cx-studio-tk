# Repository Guidelines

`cx-studio-tk` 是一个面向影视后期制作的 Python 工具集，采用 uv workspace 组织的 monorepo。
包含 `cx-studio`（基础设施）、`cx-wealthy`（Rich UI 组件）、`cxalio-studio-tools`（CLI 工具集）三个主力包，以及已废弃的 `cx-wealth`（被 `cx-wealthy` 取代）。

## 命令与环境

所有命令在 workspace 根目录执行。

### 依赖
uv sync                   # 安装/同步所有依赖
uv sync --group dev       # 安装 dev 依赖（含 black）

### 运行工具
uv run mediascout --help
uv run mediakiller --help
uv run ffpretty --help
uv run jpegger --help
uv run hostskeeper --help

### 格式化
uv run black .            # 项目中唯一格式化工具，提交前运行

### 构建
uv build                  # 构建所有包

### 测试
- ⚠️ 项目当前**没有**测试基础设施。无测试目录、无测试依赖、无 CI。
- 不要尝试运行测试命令——它们不存在。

## 项目结构

| Directory | Purpose |
|---|---|
| `packages/cx-studio/cx_studio/` | 基础设施库——值对象、FFmpeg、文件系统、IO、系统抽象 |
| `packages/cx-wealth/cx_wealth/` | Rich UI 扩展——标签、详情、帮助系统 DSL（已废弃，由 cx-wealthy 取代） |
| `packages/cxalio-studio-tools/` | CLI 工具集——应用框架 + 5 个工具（media_scout: Chain of Responsibility / media_killer: Async Mission Pipeline / jpegger: ImageFilterChain / ffpretty: FFmpeg 封装 / hosts_keeper: Plugin-based 管理） |
| `packages/cxalio-studio-tools/cx_tools/app/` | 应用生命周期框架（IApplication + IAppEnvironment） |
| `temp/` | 临时/调试文件（gitignored，勿在此编写正式代码） |

## 架构

### 依赖链
`cx-studio` ← `cx-wealthy` ← `cxalio-studio-tools`
`cx-studio` ← `cx-wealth`（已废弃，仅维护旧引用）

### CLI 应用通用生命周期（所有 6 个工具一致）
1. `[project.scripts]` 入口 → `module:run()` 函数
2. `Application.__enter__()` → `IAppEnvironment` 初始化（Rich console、SIGINT、debug 门控）
3. `Application.run(appenv)` → 解析参数 → 执行业务逻辑
4. `Application.__exit__()` → 清理

### 项目特有模式

详见 [cxalio-studio-tools CLI 工具编写规范](packages/cxalio-studio-tools/AGENTS.md)

## 开发规则

**目标平台**：Windows / macOS / Linux。涉及路径操作时使用 `pathlib.Path`，避免字符串拼接；涉及文件编码时显式指定 `encoding="utf-8"`。

### 流程

#### 执行规则
- 处理 `packages/` 下某个 workspace 的内容时，先阅读该 workspace 目录下的 `AGENTS.md`（如有）。它与本文件叠加生效——本文件是全局基线，workspace 级文件补充该工作区独有的约定、偏离点和防回退记录
- 修改代码后运行 `uv run black .`
- 为新公共函数/类添加 docstring

#### 先问再做
- 添加新依赖（`uv add`）或修改 `pyproject.toml`
- 修改版本号（`__init__.py` 中的 `__version__` 及对应 `pyproject.toml`）
- 修改分支策略相关配置（branch protection / CI workflow / git hooks）

#### 禁止项
- 直接推送到 `main` 分支——始终通过 PR
- 在生产环境运行未经测试的 CLI 工具
- 在 Box→Dataclass 桥接场景之外使用 `# type: ignore`（详见下方「数据模型选择」）
- 删除 `.env` 文件或任何非临时的配置文件（如 `pyproject.toml`、`.github/`、CI 配置）

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
- 依赖 `cx-wealthy` 的包**必须**通过 `cx_wealthy.rich_types` 引用 Rich 类型，禁止使用 `rich.table`、`rich.panel` 等原生路径；`cx_studio` 本身不依赖 `cx-wealthy`，可直接使用 Rich 原生导入

#### 数据模型选择

| 场景 | 使用 | 不使用 |
|---|---|---|
| 有固定 schema、接口契约 | `@dataclass(frozen=True)` | `dict` 或 `Box` |
| 无固定 schema、运行时结构不定 | `python-box`（`.attr` 多层访问） | 裸 `dict` |
| 序列化边界（`tomllib.load()` 返回值） | 裸 `dict` → 立即桥接为 Box/Dataclass | 保留 dict 在业务层传递 |
| Box→Dataclass 桥接 | `# type: ignore` **可接受** | — |

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
- 公开类/方法必须有 docstring；行内注释只解释代码表达不了的决策理由
- 修改代码后自底向上检查注释是否仍匹配（行内→方法→类→模块）

## 版本管理

### 版本号变量
- 每个 Python 发行包在 `__init__.py` 顶层定义 `__version__: str`（PEP 396 惯例）
- 对于有自己 `pyproject.toml` 的包（`cx-studio`、`cx-wealthy`、`cxalio-studio-tools`）：`__version__` 为版本权威来源，`pyproject.toml` 中的 `version` 须与其保持一致
- CLI 工具包（`ffpretty`、`media_scout` 等）没有独立的 `pyproject.toml`，其 `__version__` 单独管理，遵循下方的版本联动规则
- CLI 工具的 `appenv.py` 不再硬编码版本号，改为从所在包 `__init__.py` 引入：
  ```python
  from . import __version__
  self.app_version = __version__
  ```

### 版本策略
- 格式：`major.minor.patch[.hotfix]`（SemVer + 热修复段）
- 迭代版本时须更新 `__init__.py` 中的 `__version__`、`pyproject.toml` 中的 `version` 和 `CHANGELOG`
- `cx-studio` 和 `cx-wealthy`：各自 `pyproject.toml` 中独立管理版本号

#### cxalio-studio-tools — 内部联动规则
- 内部工具（media_scout、media_killer、jpegger、ffpretty、hosts_keeper）任一发生变更时：
  1. **先**修改该工具自身 `__init__.py` 中的 `__version__`
  2. **然后**响应迭代 `cxalio-studio-tools` 的 `pyproject.toml` 版本号
- 未变更的工具**不**同步修改其自身版本号

## Git 工作流

- **main** — 发布分支，只接受从 `dev` 的 `--no-ff` merge
- **dev** — 开发分支，所有功能最终合入
- **临时分支** — 从 `dev` 迁出，完整实现后 merge 回 `dev`；一般不 push 到远程
- 分支命名：`feat/<描述>`、`fix/<描述>`、`chore/<描述>`
- Commit 格式：`type(scope): 描述`（type: feat/fix/docs/chore/refactor）
- **禁止**：直接推送到 `main`

## 国际化（i18n）

项目使用 **gettext + Babel** 做 i18n，每包自持翻译文件。

### 源语言政策

**本项目以简体中文（zh_CN）为标准语言，代码中所有 `_()` 调用使用中文 msgid。**
其他语言的翻译通过 `.po` 文件的 `msgstr` 字段提供。

**注意**：由于源语言是简体中文，**不需要也不应当创建 `zh_CN` 的 `.po`/`.mo` 文件**。原因是 gettext 回退行为：找不到 `.mo` 时直接返回 msgid（即中文原文）；而空 msgstr 的 `.mo` 反而会覆盖 msgid 返回空字符串。`zh_CN` 翻译文件的存在只会引入风险，不应提交到仓库。

### 入口导入

| 所在包 | 导入路径 | 用途 |
|---|---|---|
| cx-studio | `from cx_studio.i18n import _, _ng` | 基础设施字符串 |
| cx-wealth | `from cx_wealth.i18n import _, _ng` | UI 组件字符串（旧） |
| cx-wealthy | `from cx_wealthy.i18n import _, _ng` | UI 组件字符串 |
| cx_tools（框架） | `from cx_tools.i18n import _, _ng` | 框架自身字符串 |
| media_scout | `from media_scout.i18n import _, _ng` | media_scout 工具字符串 |
| media_killer | `from media_killer.i18n import _, _ng` | media_killer 工具字符串 |
| jpegger | `from jpegger.i18n import _, _ng` | jpegger 工具字符串 |
| hosts_keeper | `from hosts_keeper.i18n import _, _ng` | hosts_keeper 工具字符串 |

工具模块**必须**从所在工具自己的 `i18n` 模块导入——`media_killer` 中的模块从 `media_killer.i18n` 导入，不交叉导入 `cx_tools.i18n`。`cx_tools` 框架自身的模块仍从 `cx_tools.i18n` 导入。

> 每个工具独立 domain 和翻译文件：domain 分别为 `cx-tools`、`media-scout`、`media-killer`、`jpegger`、`hosts-keeper`。各工具自持 `i18n/locales/`，互不交叉。

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

### 添加新字符串后的工作流

```bash
# cx-studio（在 packages/cx-studio/ 执行）
uv run pybabel extract --mapping babel.cfg --output-file cx_studio/i18n/locales/cx-studio.pot --project cx-studio --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-studio --input-file cx_studio/i18n/locales/cx-studio.pot --output-dir cx_studio/i18n/locales
uv run pybabel compile --domain cx-studio --directory cx_studio/i18n/locales

# cx-wealth（在 packages/cx-wealth/ 执行）
uv run pybabel extract --mapping babel.cfg --output-file cx_wealth/locales/cx-wealth.pot --project cx-wealth --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-wealth --input-file cx_wealth/locales/cx-wealth.pot --output-dir cx_wealth/locales
uv run pybabel compile --domain cx-wealth --directory cx_wealth/locales

# cxalio-studio-tools — 每个工具分别提取（在 packages/cxalio-studio-tools/ 执行）
uv run pybabel extract -k _ --output-file cx_tools/i18n/locales/cx-tools.pot cx_tools/
uv run pybabel extract -k _ --output-file media_scout/i18n/locales/media-scout.pot media_scout/
uv run pybabel extract -k _ --output-file media_killer/i18n/locales/media-killer.pot media_killer/
uv run pybabel extract -k _ --output-file jpegger/i18n/locales/jpegger.pot jpegger/
uv run pybabel extract -k _ --output-file hosts_keeper/i18n/locales/hosts-keeper.pot hosts_keeper/

# 然后对每个工具 update 和 compile
uv run pybabel update -i cx_tools/i18n/locales/cx-tools.pot -d cx_tools/i18n/locales -l en_US -D cx-tools
uv run pybabel compile -d cx_tools/i18n/locales -l en_US -D cx-tools
# （对 media_scout、media_killer、jpegger、hosts_keeper 重复同样操作）
```

编译出的 `.mo` **必须提交到 git**——用户安装时不执行编译。

### 帮助文本

帮助文本（help.md）不通过 gettext，而是使用文件后缀区分语言。`load_localized_text()` 根据 locale 自动选择：

```python
from cx_studio.i18n import load_localized_text
md = load_localized_text(__package__, "help.md")
```

翻译者将 `help.md` 复制为 `help.en_US.md`，逐段翻译。
