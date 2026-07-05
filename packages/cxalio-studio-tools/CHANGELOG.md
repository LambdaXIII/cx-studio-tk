# Change Log of Cxalio Studio Tools



### v0.8.6

- FFpretty 迭代至 0.8.6，MediaScout 迭代至 0.8.6
- **依赖迁移**：ffpretty 和 media_scout 的 TUI 依赖从 `cx-wealth` 迁移至 `cx-wealthy`（`WealthHelp`→`WealthyHelp`、`WealthLabel`→`RichLabel`、`WealthDetailPanel`/`WealthDetailTable`/`IndexedListPanel` 导入路径更新）
- **API 适配**：`HelpGroup.add_action` 的 `description=` 参数更名为 `detail=`（media_scout/arg_parser.py 中 10 处适配）
- **样式统一**：硬编码颜色样式（`red`/`yellow`/`green`/`blue`/`bright_black`/`cyan`/`dim`/`green1`）替换为 `cx_wealthy` 主题语义样式（`cx.error`/`cx.warning`/`cx.success`/`cx.info`/`cx.debug`/`cx.number`/`cx.whisper`/`cx.argument`/`cx.filepath`），颜色选择委托给主题

### v0.8.5

- HostsKeeper 迭代至 0.8.5
- **帮助系统重构**：`app_help.py` 从扁平参数结构迁移至 `CommandGroup`，usage 行正确展示子命令列表（`list|show|edit|update|new`），每个子命令的专有参数正确归属
- **修复遗漏**：补充 `new` 命令的帮助定义（此前 parser 支持但 help 未显示）
- **修复命名不一致**：搜索参数名从 `--search-pattern` 修正为 `-s, --search`（与 `appcontext.py` 一致）
### v0.8.4

- HostsKeeper 迭代至 0.8.4
- **重构并发模型**：移除 contenter 级并发（原 `asyncio.as_completed` 因同步 `urlopen` 阻塞事件循环形同虚设），简化为 profile 级并发（`max_workers` 控制同时处理的 profile 数），profile 内 contenter 顺序处理
- **解除 URL 阻塞**：`UrlContenter.get_content()` 改为 async，通过 `run_in_executor` 将 `urlopen` 移出事件循环，使多 profile 并行下载真正生效
- **Progress 实时追踪**：`hostskeeper update` 集成 Rich Progress 面板，单 contenter 用回转 spinner，多 contenter 用进度条，实时显示每个 profile 的处理状态
- **迁移至 cx_wealthy**：hosts_keeper 的 TUI 依赖从 `cx-wealth` 完整迁移至 `cx-wealthy`（`WealthLabel`→`RichLabel`、`WealthHelp`→`WealthyHelp`），样式通过 `default_theme` 机制注入
- **cx_wealthy.rich_types 补充**：新增 `Progress`、`TaskID`、`SpinnerColumn`、`TextColumn`、`BarColumn`、`TaskProgressColumn`、`TimeRemainingColumn` 导出
- **contenter 动态状态文本**：`AbstractContenter` 新增 `status_text` 属性，contenter 在处理过程中自行更新，外部通过回调读取以实时更新 progress description
- **修复 HostsSaver 先使用后赋值 bug**：`__init__` 中 else 分支（`source_hosts` 为 `Iterable[str]` 时）先写入临时文件再赋值
- **修复 i18n 遗漏**：`appenv.py` 中 2 处临时目录提示文字、`application.py` 中 `command_list` 表头（ID/Name/Description/Enabled）
- **修复拼写错误**：`prepare_customed_lines` → `prepare_custom_lines`
- **修复缺失类型标注**：`AppContext.show_help`
- **删除死代码**：`application.py` 中未使用的 `url = f"file://{file_path.resolve()}"`
### v0.8.3

- Jpegger 迭代至 0.8.3
- 配合 cx-wealthy 0.1.2 的 `__rich_detail__` str/Text 语义变更：`ImageFilterChain.__rich_detail__` 的 key 改为 yield `Text.from_markup(...)` 对象，保持彩色标签显示
- 修复 jpegger 输出文件重名时的行为：不再自动下划线重命名，改为跳过并警告

### v0.8.2

- Jpegger 迭代至 0.8.2
- 将 Jpegger 的 Rich UI 依赖从 `cx-wealth` 迁移至 `cx-wealthy`（其余 4 个工具仍在 cx-wealth 上，渐进迁移）
- 在 `cxalio-studio-tools` 的 `dependencies` 中新增 `cx-wealthy`，保留 `cx-wealth`
- 在 `IAppEnvironment` 中合并 `cx_wealthy.default_theme`，使应用框架层支持 cx_wealthy 组件渲染
- 修复迁移过程中发现的 cx_wealthy 阻塞性问题（详见 spec 同目录 `audit.md`）：
  - `Group` 类新增 `add_action` 便利方法（延迟导入保持分层）
  - `Action._validate_flags` 放宽校验，支持位置参数名与含连字符的 flag（如 `--force-overwrite`）

### v0.8.1

- Jpegger 迭代至 0.8.1
- 修复 `ResizeFilter` 与 `FactorResizeFilter` 的缩放逻辑：按目标尺寸/缩放因子计算宽高，避免原图尺寸覆盖或传入浮点数导致 `Image.resize` 失败
- 修复 `Mission.filter_chain` 默认共享可变对象的问题，确保每个任务实例拥有独立的过滤器链
- 为 Jpegger 各模块、类、方法补充文档字符串，并在关键执行路径增加说明，提升可维护性
- 修复 `IAppEnvironment` 未从 `cx_tools.app` 正确导出的问题
- 在分发包 `pyproject.toml` 中配置 basedpyright，关闭 `reportUnknownMemberType` 与 `reportExplicitAny` 规则
- 在代码注释中说明：GIF 仅处理第 1 帧为期望行为，Jpegger 的定位是单帧图片处理

### v0.8.0

- HostsKeeper 更新 hosts 后自动执行平台对应的 DNS 缓存刷新（Windows ipconfig /flushdns、macOS killall -HUP mDNSResponder、Linux 提示手动命令）
- 新增 `--skip-flush` 参数，跳过自动刷新仅给出平台特定的手动命令提示
- 帮助文档（--help / --tutorial）中补充 `--skip-flush` 说明
- 所有提示信息仅在系统 hosts 路径更新时触发，自定义 `-t` 路径不触发

- 修复多处 hosts 文件编码处理问题（移除冗余的 platform encoding 检测、强制关闭 BOM 写入、补齐 importlib.resources 显式编码参数）

### v0.7.5

- 修复 MediaKiller 任务执行器中 finally 块的 return 语句问题
- 配置 pyright 类型检查并修复类型安全问题
- 扩展 Python 版本支持范围至 <3.15

### v0.7.1

- 修复了 HostsKeeper 工具处理 URL 内容时的编码问题

### v0.7.0

- 重新调整部分代码以适应cx-studio的更新。
- 去除了 dydantic 的依赖，重新使用轻量的 dataclass。

### v0.6.3.2

- 增加了 HostsKeeper 工具保存 hosts 文件的方法，现在将在需要时调用管理员权限（仅支持sudo）
- 增加了 HostsKeeper 工具指定目标文件的参数，不指定的话仍然是系统hosts文件。
- 修复了 帮助信息中的 typo

### v0.6.2

- 增加了 HostsKeeper 工具，用于管理 hosts 文件
- 为 IAppEnvironment 增加了判断当前用户是否为管理员的方法

### v0.5.1.6

- 为 ffpretty 增加了取消操作的提示信息
- 为 ffpretty 增加了查询模式
- 为 ffpretty 增加了帮助信息
- 为 ffpretty 清理了代码

### v0.5.1.4

- 全面排查bug
- 将默认样式定义为全局主题 cx_default_theme
- 优化了 mediakiller 中的一些输出方式

### v0.5.1.3

- 增加了 CxHighlighter 类，用于高亮显示 CX 相关的日志信息
- 自动安装 CxHighlighter 作为全局输出的高粱显示工具，默认情况下不影响 WealthHelp 的输出

### v0.5.1.2

- 为 Jpegger 定义了无事可做时的处理方式

### v0.5.1.1

- 增加了 Jpegger 工具，用于快速批量转换图片
- 调整了代码格式

### v0.5.0.4

- 修改 mediakiller 的任务保存格式为 XML 格式
- 修改 ConfigManager 的默认配置文件保存位置，增加了一级子目录
- 调整了 mediakiller 中 import 的顺序，避免载入 bug

### v0.5.0.3

- hotfix: mediakiller 文件大小统计的输出 bug
- hotfix: 尝试修复任务自动保存在 macOS 上的 bug

### v0.5.0.1

- 修正错误的 import
- 为 mediakiller 增加文件大小统计功能

### v0.4.9.5

- 全面使用 pydantic 和 Box 替代原生和 cx-studio 的实现

### v0.4.9.4

- hot fix for a packaging bug

### v0.4.9.3

- 修复了 Media Killer 提示信息的 bug
- 增加了 FFpretty 工具

### v0.4.9.1

- Media Scout 现在可以选择输出转义模式了
