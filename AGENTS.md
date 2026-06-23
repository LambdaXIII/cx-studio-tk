# Repository Guidelines

## Project Overview

`cx-studio-tk` 是一个面向影视后期制作的 Python 工具集，采用 uv workspace 组织的 monorepo。包含三个包：

- **cx-studio** (v0.7.5) — 基础设施类库，提供时间/文件大小/FFmpeg/IO/文本/系统抽象等基础能力
- **cx-wealth** (v0.7.5) — Rich 终端的 UI 组件扩展（标签、详情面板、动态列、索引列表、帮助系统 DSL）
- **cxalio-studio-tools** (v0.7.5) — 可直接使用的 CLI 工具集（媒体文件扫描/转码、图片批处理、Hosts 管理、FFmpeg 封装等）

依赖链：`cx-studio` ← `cx-wealth` ← `cxalio-studio-tools`。

## Architecture & Data Flow

### 依赖架构

```
cx-studio-tk (root meta-package)
 ├─ packages/cx-studio          — 基础设施库，无 CLI 入口
 │   ├─ core/                   时间/文件大小/时间范围/时间基值对象
 │   ├─ ffmpeg/                 FFmpeg 封装（sync + async，基于 pyee EventEmitter）
 │   ├─ filesystem/             路径工具/文件缓存/编码检测/路径扩展器（Validator 模式）
 │   ├─ iotools/                流式 IO（sync + async 双实现）
 │   ├─ text/                   文本工具 + 标签模板替换引擎
 │   ├─ number/                 数值范围/快速数学工具
 │   ├─ system/                 跨平台抽象（SystemType 枚举，CrossRunner 派发）
 │   ├─ collectiontools/        函数式集合工具
 │   ├─ tui/                    异步取消令牌/双击检测/任务计数器
 │   └─ locales/                gettext i18n（en_US）
 │
 ├─ packages/cx-wealth           — Rich 扩展，提供可复用 UI 组件
 │   ├─ wealth_label.py         Protocol mixin + 标签展平渲染
 │   ├─ wealth_detail.py        Protocol mixin → Table/Panel 键值展示
 │   ├─ dynamic_columns.py      自适应列数布局
 │   ├─ indexed_list_panel.py   索引列表面板
 │   └─ wealth_help/            树形帮助系统 DSL（_Node → _Group/_Action/_Note）
 │
 └─ packages/cxalio-studio-tools — CLI 工具集
     ├─ cx_tools/app/           Application 框架层（IApplication + IAppEnvironment 契约）
     ├─ media_scout/            Chain of Responsibility 文件检查器链
     ├─ media_killer/           Async Mission Pipeline（FFmpeg 批量转码）
     ├─ jpegger/                ImageFilterChain（PIL 图片批处理）
     ├─ ffpretty/               FFmpeg 转码/探针封装
     ├─ hosts_keeper/           Plugin-based Hosts 管理
     └─ cx_tools/               FileSizeCounter 工具
```

### 数据流模式

**CLI 应用通用生命周期**（所有 6 个工具一致）：

1. `[project.scripts]` 入口 → `module:run()` 函数
2. `Application.__enter__()` → `IAppEnvironment` 初始化（Rich console、SIGINT、debug 门控）
3. `Application.run(appenv)` → 解析参数 → 执行业务逻辑
4. `Application.__exit__()` → 清理

**media_killer 流水线**（最复杂的示例）：

```
InputScanner → MissionMaker（async 展开源/替换标签）→ MissionArranger（排序去重）
→ MissionMaster（asyncio semaphore 限流并行）→ MissionRunnerEach（FFmpegAsync 执行）
```

### 同步/异步边界

- `cx-studio` 为关键组件提供 sync + async 双实现：`FFmpeg`/`FFmpegAsync`、`StreamUtils`/`AsyncStreamUtils`
- CLI 工具在 run 层使用 `asyncio.run()`，上层异步、下层可以根据需要选择 sync 或 async

## Key Directories

| Directory | Purpose |
|---|---|
| `packages/cx-studio/cx_studio/` | 核心类库 - 值对象、FFmpeg 封装、文件系统、IO 流 |
| `packages/cx-wealth/cx_wealth/` | Rich UI 组件 - 标签、详情、帮助系统 |
| `packages/cxalio-studio-tools/` | CLI 工具 - 应用框架 + 5 个具体工具 |
| `packages/cxalio-studio-tools/cx_tools/app/` | 应用生命周期 ABC + ConfigManager + SafeError |
| `temp/` | 临时/调试文件（gitignored） |

## Development Commands

```bash
# 安装/同步依赖（uv workspace 根目录执行）
uv sync

# 安装 dev 依赖
uv sync --group dev

# 运行 CLI 工具（开发模式）
uv run mediascout --help
uv run mediakiller --help
uv run ffpretty --help
uv run jpegger --help
uv run hostskeeper --help

# 格式化
uv run black .

# 进入 venv
.venv\Scripts\activate  # Windows
```

**注意**：项目尚未配置测试框架、linter 或 type checker。`uv.lock` 被 gitignored（不推荐——对应用项目应提交 lock 文件）。

## Code Conventions & Common Patterns

### 命名约定

- **模块文件**: `cx_<area>.py` 前缀（如 `cx_time.py`, `cx_pathutils.py`）——camelCase 文件名
- **类**: PascalCase（`FileSize`, `CxTime`, `WealthDetailPanel`）
- **函数/方法**: snake_case（`from_milliseconds()`, `detect_file_encoding()`）
- **ABC/接口**: `I` 前缀（`IApplication`, `IAppEnvironment`, `ITimeRange`, `IPathValidator`）
- **Protocol**: `XxxMixin` 后缀（`WealthLabelMixin`, `WealthDetailMixin`, `RichPrettyMixin`）
- **私有模块**: `_` 前缀（`_Node`, `_Group`, `_Action`）

### 类型标注

- 全量使用 type hints（Python 3.10+ union syntax: `X | Y`, `Self`, `ClassVar`, `Literal`, `dataclass`）
- 使用 `@runtime_checkable` Protocol 进行鸭子类型检测（cx-wealth 核心模式）
- 使用 `StrEnum`（系统类型枚举）

### 值对象模式

核心领域类型采用不可变/半不可变值对象 + 静态工厂：

```python
# CxTime: 毫秒时间值对象
t = CxTime.from_seconds(90.5)       # factory
t.total_milliseconds                 # → 90500
t.pretty_string(locale="zh_CN")     # → "1 分钟 30 秒 500 毫秒"
t.to_timecode(Timebase(25))         # → "00:01:30:12"

# FileSize: 字节大小值对象
s = FileSize.from_megabytes(1.5, standard="binary")
s.pretty_string()                    # → "1.50 MiB"
```

### EventEmitter 模式（FFmpeg）

`FFmpeg` 和 `FFmpegAsync` 继承 `pyee.EventEmitter`/`AsyncIOEventEmitter`，派发事件：

```python
ff = FFmpeg()
ff.on("progress_updated", lambda info: print(info.percent))
ff.on("finished", lambda: print("done"))
ff.execute(["-i", "input.mp4", "output.avi"])
```

同步版使用 `ThreadPoolExecutor` 消费子进程 stderr，异步版使用 `asyncio.subprocess`。

### 跨平台派发（CrossRunner）

```python
from cx_studio.system import CrossRunner, SystemType

open_file = CrossRunner()
open_file.register_function(SystemType.WINDOWS, os.startfile)
open_file.register_function(SystemType.MACOS,  lambda p: subprocess.run(["open", p]))
```

### 应用框架模式（所有 CLI 工具统一）

```python
class Application(IApplication):
    async def run(self, appenv: IAppEnvironment):
        appenv.say("Processing...")       # Rich console.print, 始终显示
        appenv.whisper("debug info")      # 仅 debug 模式显示
```

AppEnv 单例提供：Rich console、`say()`/`whisper()`、`interrupt_handler()`（双击 Ctrl+C 强制退出）、`is_debug_mode_on()`。

### 帮助系统模式（cx-wealth WealthHelp）

每个工具定义自己的 `XxxHelp(WealthHelp)` 子类：

```python
class MKHelp(WealthHelp):
    def __init__(self):
        super().__init__(prog="mediakiller", description="Batch media transcoder")
        root = self.help_group
        general = root.add_group("General options")
        general.add_action(["-d", "--debug"], description="Enable debug mode")
```

支持 `-h`（紧凑用法）和 `--tutorial`/`--full-help`（详细视图，通过 `importlib.resources` 加载 markdown）。

### 异常处理

- **SafeError** — 可恢复的应用级异常，带 style，被 `Application.__exit__` 捕获
- **FFmpegError** — 带子类自动匹配工厂 `create(msg)`：根据正则匹配自动选择 `FFmpegFileNotFoundError` / `FFmpegNoExecutableError` 等
- 使用 `rich.traceback.install()` 在 CLI 入口点启用 Rich traceback

### 数据类偏好

广泛使用 `dataclass(frozen=True)` 作数据容器：

```python
@dataclass(frozen=True)
class Mission:
    ulid: str
    preset_name: str
    source: Path
    target: Path
    args: ArgumentGroup
```

TOML 配置文件通过 `tomllib` + `python-box` 解析为 dataclass（media_killer preset, hosts_keeper profile）。

### 包内导入惯例

每个子包通过 `__init__.py` star-import 汇聚所有公开符号。`cx-wealth/rich_types.py` 作为单一 Rich 类型再导出中心。

## Important Files

| File | Significance |
|---|---|
| `pyproject.toml` | 根 workspace 配置，dev deps（black），注释掉的 pytest 配置 |
| `packages/cx-studio/pyproject.toml` | 类库构建配置 |
| `packages/cx-wealth/pyproject.toml` | CLI 工具构建 + entry point |
| `packages/cxalio-studio-tools/pyproject.toml` | CLI 工具构建 + 5 entry points + hatch build 配置 |
| `packages/cx-studio/cx_studio/core/cx_time.py` | CxTime 核心值对象 |
| `packages/cx-studio/cx_studio/core/cx_filesize.py` | FileSize 核心值对象 |
| `packages/cx-studio/cx_studio/ffmpeg/cx_ffmpeg.py` | FFmpeg sync 封装 |
| `packages/cx-studio/cx_studio/ffmpeg/cx_ffmpeg_async.py` | FFmpeg async 封装 |
| `packages/cx-studio/cx_studio/filesystem/cx_file_info_cache.py` | SQLite 文件元缓存 |
| `packages/cx-wealth/cx_wealth/wealth_help/w_help.py` | WealthHelp 帮助系统入口 |
| `packages/cxalio-studio-tools/cx_tools/app/iapplication.py` | IApplication ABC |
| `packages/cxalio-studio-tools/cx_tools/app/iappenv.py` | IAppEnvironment ABC |
| `packages/cxalio-studio-tools/media_killer/components/mission_master.py` | async 并行 FFmpeg 编排器 |
| `packages/cxalio-studio-tools/media_scout/inspectors/inspector_chain.py` | Chain of Responsibility 示例 |

## Runtime/Tooling Preferences

- **Python**: ≥3.12, <3.14
- **Package manager**: `uv`（workspace 管理，`uv sync` 安装）
- **Build system**: `hatchling`（所有包统一）
- **Formatter**: `black>=25.1.0`（root dev dep，项目中唯一格式化工具）
- **Formatter command**: `uv run black .`
- **IDE**: VSCode（配置了 `pytestEnabled`，但无实际测试目录）
- **OS**: 跨平台（Windows/macOS/Linux），system 模块显式检测 SystemType
- **gitignore 重要项**: `uv.lock`、`/temp/`、`.codegraph/`、`py.typed`、IDE 目录

## Testing & QA

> ⚠️ **项目当前`没有`测试基础设施。**

- 无测试目录、无测试文件、无测试依赖
- `pyproject.toml` 中 pytest 配置被注释掉
- VSCode settings 声明了 `pytestEnabled: true` 但实际无测试
- 唯一代码质量工具是 `black`（格式化）
- 不存在 CI 配置文件

添加测试时的建议：

```python
# 测试框架：pytest（依赖已经在注释中提及）
# 运行方式：
uv run pytest tests/
```

## 补充说明

- 项目描述在根 `pyproject.toml` 中仍是占位符（`"Add your description here"`）
- 版本号全局跟踪 0.7.x，但 `cx-wealth` 的 CHANGELOG 停在 0.1.x
- 许可证：GPLv3 + 附加条款（分发修改版本须改名、保留版权声明）
- i18n：cx-studio 包含 Babel `.pot` 文件和 en_US 编译的 `.mo` 文件
### 版本策略

版本号遵循语义化版本（SemVer），但采用 monorepo 统一步调：
  - 根 `pyproject.toml`（`cx-studio-tk`）持有**总体版本号**
  - **任何代码库变更**（无论涉及哪个包）都触发总体版本号更新
  - 本次有变更的包同步更新为总体版本号
  - 未变更的包保持原有版本不变
  - 版本号在当前序列中递增——无功能变更时跳 patch（如 `0.7.0 → 0.7.5`），有功能/破坏性变更时跳 minor/major
  - 此策略确保所有包版本可互相追踪，同时避免不必要的全量发布
