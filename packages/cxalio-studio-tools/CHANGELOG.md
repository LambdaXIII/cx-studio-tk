# Change Log of Cxalio Studio Tools

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
