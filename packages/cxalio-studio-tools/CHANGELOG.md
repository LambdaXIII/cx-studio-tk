# Change Log of Cxalio Studio Tools


### v0.6.3

 - 增加了 HostsKeeper 工具保存 hosts 文件的方法，现在将在需要时调用管理员权限（仅支持sudo）
 - 增加了 HostsKeeper 工具指定目标文件的参数，不指定的话仍然是系统hosts文件。

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
