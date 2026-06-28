# Repository Guidelines

`cx-studio-tk` 是一个面向影视后期制作的 Python 工具集，采用 uv workspace 组织的 monorepo。包含三个包：`cx-studio`（基础设施类库）、`cx-wealth`（Rich UI 组件扩展）、`cxalio-studio-tools`（CLI 工具集）。

## Commands

所有命令在 workspace 根目录执行。

### 环境与依赖
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

## Boundaries

### Always do
- 修改代码后运行 `uv run black .`
- 为新公共函数/类添加 docstring

### Ask first
- 添加新依赖（`uv add`）或修改 `pyproject.toml`
- 修改版本号（`pyproject.toml` 或各包 `__init__.py` 中的 `__version__`）
- 修改分支策略相关配置（branch protection / CI workflow / git hooks）

### Never do
- 直接推送到 `main` 分支——始终通过 PR
- 在生产环境运行未经测试的 CLI 工具
- 在 Box→Dataclass 桥接场景之外使用 `# type: ignore`（详见下方「数据模型选择」）
- 删除 `.env` 文件或任何非临时的配置文件（如 `pyproject.toml`、`.github/`、CI 配置）

## Project Structure

| Directory | Purpose |
|---|---|
| `packages/cx-studio/cx_studio/` | 基础设施库——值对象、FFmpeg、文件系统、IO、系统抽象 |
| `packages/cx-wealth/cx_wealth/` | Rich UI 扩展——标签、详情、帮助系统 DSL |
| `packages/cxalio-studio-tools/` | CLI 工具集——应用框架 + 5 个工具（media_scout: Chain of Responsibility / media_killer: Async Mission Pipeline / jpegger: ImageFilterChain / ffpretty: FFmpeg 封装 / hosts_keeper: Plugin-based 管理） |
| `packages/cxalio-studio-tools/cx_tools/app/` | 应用生命周期框架（IApplication + IAppEnvironment） |
| `temp/` | 临时/调试文件（gitignored，勿在此编写正式代码） |

## Architecture

### 依赖链
`cx-studio` ← `cx-wealth` ← `cxalio-studio-tools`（箭头指向依赖者，即 `cxalio-studio-tools` 依赖 `cx-wealth` 依赖 `cx-studio`）

### CLI 应用通用生命周期（所有 6 个工具一致）
1. `[project.scripts]` 入口 → `module:run()` 函数
2. `Application.__enter__()` → `IAppEnvironment` 初始化（Rich console、SIGINT、debug 门控）
3. `Application.run(appenv)` → 解析参数 → 执行业务逻辑
4. `Application.__exit__()` → 清理

### 项目特有模式
- **CLI 入口点**：每个工具在 `__init__.py` 定义 `run()` → `rich.traceback.install()` → `Application` 上下文管理器。`Application` 命名随工具变化（`Application`、`FFPrettyApp`、`JpeggerApp`），但均实现 `IApplication`。
- **参数解析**：每个工具使用 `AppContext` 类（`from_arguments()` 唯一工厂，`kwargs` 白名单赋值），不直接暴露 argparse。
- **帮助系统**：每个工具使用 `WealthHelp` DSL（`add_group`/`add_action`/`add_note` 声明式构建），帮助文件通过 `importlib.resources.read_text()` 加载。
- **异常体系**：`SafeError`（可恢复应用异常，带 style）由 `Application.__exit__` 捕获；`FFmpegError` 子类通过正则自动匹配工厂 `create(msg)`。
- **分级输出**：`IAppEnvironment` 提供 `say()`（始终显示）和 `whisper()`（仅 debug 模式）两个输出层级。

## Code Conventions

### 命名约定
- 类：PascalCase；函数/方法：snake_case
- 供他人 import 的依赖模块/包使用库名缩写前缀（如 `cx_`、`wealth_`）以避免与使用者的模块重名；`cx_tools` 应用框架同样遵循此惯例。纯 CLI 入口工具（media_scout、media_killer 等）不受此限。
- ABC/接口：`I` 前缀（IApplication、IAppEnvironment、ITimeRange、IPathValidator）
- 私有类/函数：`_` 前缀（_Node、_Group）

### 类型标注
- 全量 type hints；Python 3.10+ union syntax（`X | Y`）；`@override`（PEP 698，3.12+）
- 从 `collections.abc` 导入集合类型，不使用 `typing` 中已废弃的同名等价物

### 导入规则
- 每个子包通过 `__init__.py` star-import 汇聚所有公开符号
- 通用包使用别名导入，将符号来源带到调用点：
  - `r` → `cx_wealth.rich_types`（Rich 类型统一出口）
  - `tt` → `cx_studio.text`（文本工具）
- 依赖 `cx-wealth` 的包**必须**通过 `cx_wealth.rich_types` 引用 Rich 类型，禁止使用 `rich.table`、`rich.panel` 等原生路径；`cx_studio` 本身不依赖 `cx_wealth`，可直接使用 Rich 原生导入

### 数据模型选择

| 场景 | 使用 | 不使用 |
|---|---|---|
| 有固定 schema、接口契约 | `@dataclass(frozen=True)` | `dict` 或 `Box` |
| 无固定 schema、运行时结构不定 | `python-box`（`.attr` 多层访问） | 裸 `dict` |
| 序列化边界（`tomllib.load()` 返回值） | 裸 `dict` → 立即桥接为 Box/Dataclass | 保留 dict 在业务层传递 |
| Box→Dataclass 桥接 | `# type: ignore` **可接受** | — |

**硬约束**：`# type: ignore` **仅允许**在 Box→Dataclass 桥接边界使用。项目其他位置禁止无理由使用。

### 展示协议
- `__rich_label__()` → 紧凑标签（yield Renderable 片段，用于列表行标题）
- `__rich_detail__()` → 详情面板（yield `(key, value)` 二元组，渲染为两列表格）
- 两者可共存；核心领域类型（Mission、Preset、StreamInfo）应同时实现。可通过 `yield from super().__rich_label__()` 复用父类标签。

### 文档与注释
- 公开类/方法必须有 docstring；行内注释只解释代码表达不了的决策理由
- 修改代码后自底向上检查注释是否仍匹配（行内→方法→类→模块）

## Git Workflow

- **main** — 发布分支，只接受从 `dev` 的 `--no-ff` merge
- **dev** — 开发分支，所有功能最终合入
- **临时分支** — 从 `dev` 迁出，完整实现后 merge 回 `dev`；一般不 push 到远程
- 分支命名：`feat/<描述>`、`fix/<描述>`、`chore/<描述>`
- Commit 格式：`type(scope): 描述`（type: feat/fix/docs/chore/refactor）
- **禁止**：直接推送到 `main`

## 补充

### 版本策略
- 格式：`major.minor.patch[.hotfix]`（SemVer + 热修复段）
- monorepo 统一步调：根 `pyproject.toml` 持总体版本号，任何变更触发其更新；本次有变更的包同步更新，未变更的保持不变
### 运行环境
- **Python**: ≥3.12, <3.15
- **Package manager**: `uv`（workspace 管理）
- **Build system**: `hatchling`
- **Formatter**: `black>=25.1.0`（唯一格式化工具）
- **OS**: 跨平台（Windows/macOS/Linux）
- **许可证**: GPLv3 + 附加条款（分发修改版本须改名、保留版权声明）

### 测试
- ⚠️ 项目当前**没有**测试基础设施。无测试目录、无测试依赖、无 CI。
- 不要尝试运行测试命令——它们不存在。

## 国际化与本地化（i18n/l10n）

项目使用 **gettext + Babel** 做 i18n，每包自持翻译文件。

### 源语言政策（硬约束）

**本项目以简体中文（zh_CN）为标准语言，代码中所有 `_()` 调用使用中文 msgid。**

不接受以下做法：
- 以英文为 msgid、中文为 msgstr
- 所谓"开源项目应该用英文"的惯例
- 将中文放在次级地位的翻译工作流

英文等其他语言的翻译通过 `.po` 文件的 `msgstr` 字段提供，与代码本身无关。
翻译者的工作是翻译中文到目标语言，而不是等待英文翻译再转翻。

### 入口导入

| 所在包 | 导入路径 | 用途 |
|---|---|---|
| cx-studio | `from cx_studio.i18n import _, _ng` | 基础设施字符串 |
| cx-wealth | `from cx_wealth.i18n import _, _ng` | UI 组件字符串 |
| cxalio-studio-tools | `from cx_tools.i18n import _, _ng` | CLI 工具字符串 |

不要在包间交叉导入翻译函数——`cx_tools` 中的模块必须从 `cx_tools.i18n` 导入，不从 `cx_studio.i18n` 导入。

> `cx_tools` 是 `cxalio-studio-tools` 分发包内各工具（media_scout、media_killer 等）的共享框架层。之所以 i18n 放在 `cx_tools` 而非各工具各自独立，是因为 domain 统一为 `cx-tools`，所有工具的字符串使用同一份 .po 文件翻译，避免碎片化。`cx_tools.i18n` 服务的是整个分发包，而非仅 `cx_tools` 自身。

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
uv run pybabel extract --mapping babel.cfg --output-file cx_studio/locales/cx-studio.pot --project cx-studio --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-studio --input-file cx_studio/locales/cx-studio.pot --output-dir cx_studio/locales
uv run pybabel compile --domain cx-studio --directory cx_studio/locales

# cx-wealth（在 packages/cx-wealth/ 执行）
uv run pybabel extract --mapping babel.cfg --output-file cx_wealth/locales/cx-wealth.pot --project cx-wealth --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-wealth --input-file cx_wealth/locales/cx-wealth.pot --output-dir cx_wealth/locales
uv run pybabel compile --domain cx-wealth --directory cx_wealth/locales

# cxalio-studio-tools（在 packages/cxalio-studio-tools/ 执行）
uv run pybabel extract --mapping babel.cfg --output-file cx_tools/locales/cx-tools.pot --project 'cxalio-studio-tools' --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-tools --input-file cx_tools/locales/cx-tools.pot --output-dir cx_tools/locales
uv run pybabel compile --domain cx-tools --directory cx_tools/locales
```

编译出的 `.mo` **必须提交到 git**——用户安装时不执行编译。

### 帮助文本

帮助文本（help.md）不通过 gettext，而是使用文件后缀区分语言。`load_localized_text()` 根据 locale 自动选择：

```python
from cx_studio.i18n import load_localized_text
md = load_localized_text(__package__, "help.md")
```

翻译者将 `help.md` 复制为 `help.en_US.md`，逐段翻译。
