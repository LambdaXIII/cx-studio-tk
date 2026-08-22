# cx-studio

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

基础设施库，为影视后期自动化工具的开发提供通用组件。

## 安装

```bash
pip install cx-studio
```

要求 Python >= 3.12, < 3.15。

## 模块

### core — 核心值对象

- **CxTime**：SMPTE 时码解析与计算，支持 23.976 / 24 / 25 / 29.97 / 30 / 50 / 59.94 / 60 fps 等常见帧率。
- **Timebase**：帧率抽象（fps + drop_frame），提供 `from_fps()` 工厂从帧率构造。
- **TimeRange**：时间区间运算，支持重叠检测、包含判断、时点与区间的关系判定。
- **FileSize**：文件大小的类型化表示，支持 binary（KiB/MiB/GiB）与 international（KB/MB/GB）两种标准，提供 `pretty_string()` 人类可读输出。
- **NumberRange**：带边界的数值范围对象，支持跨区间映射、百分比转换与 clamp 裁剪。
- **quick_clamp / quick_remap**：便捷数值函数，功能类似 AE 表达式中的 clamp 与 remap。
- **flatten_list / iter_with_separator / split_to_two**：集合工具——递归展平、迭代间插分隔符、按谓词拆分序列。

### text — 文本工具

- **TagReplacer**：模板标签替换系统，支持从对象属性、路径信息、环境变量等来源动态渲染文本（配套 `PathInfoProvider`）。
- **auto_quote / auto_unquote / auto_list_text / auto_unwrap**：智能引号添加与去除、文本按分隔符拆分与去换行。
- **random_string**：随机字符串生成。
- **escape_arg / join_args**：命令行参数转义与拼接。

### filesystem — 文件系统工具

- **PathUtils**：路径工具命名空间（规范化、后缀处理、引号包裹、父目录/基线提取等）。
- **PathExpander**：路径展开，支持通配符、环境变量和用户目录（`~`）。
- **CmdFinder**：可执行文件查找，遍历 PATH 并检测有效后缀。
- **SuffixFinder**：文件后缀匹配。
- **FileList / FileSizer / FileInfoCache**：文件列表、大小计算与信息缓存。
- **detect_file_encoding**：基于 chardet 的文本编码探测。

### system — 系统抽象

- **SystemType**：平台枚举，区分 Windows / macOS / Linux / WSL / iOS / Android / FreeBSD。
- **CrossRunner**：跨平台命令执行封装。
- **system_open**：跨平台文件或 URL 打开（`xdg-open` / `open` / `start`）。
- **is_user_admin**：跨平台管理员权限检测。

### process — 子进程与流处理

跨平台的子进程创建（Windows 下自动配置 `CREATE_NEW_PROCESS_GROUP` 以支持信号发送）、流式读写、字节流记录与重定向。同步（`StreamUtils`）与异步（`AsyncStreamUtils`）两组接口。

### clikit — CLI 基础设施

- **DoubleTrigger**：CLI 双击触发组件，与 `FIRST_TRIGGERED` / `SECOND_TRIGGERED` 状态常量配合实现双击判定。

### ffmpeg — FFmpeg 封装

- **FFmpegAsync**：异步 FFmpeg 执行器。
- **FFmpegCodingInfo / FFmpegProcessInfo / FFmpegFormatInfo**：编码信息、进程信息、格式信息值对象。
- **FFmpegArgumentsPreProcessor**：参数预处理，处理引号兼容性与 Windows 路径适配。

### i18n — 国际化

基于 gettext 的翻译基础设施，提供 `_()` 和 `_ng()`（复数）函数，以及 `detect_locale()`（locale 检测）和 `load_localized_text()`（本地化文本加载器）。简体中文为源语言。

## 链接

返回项目首页：[cx-studio-tk](../..)
