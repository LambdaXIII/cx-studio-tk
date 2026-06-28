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
- **FileSize**：文件大小的类型化表示，支持 binary（KiB/MiB/GiB）与 international（KB/MB/GB）两种标准，提供 `pretty_string()` 人类可读输出。
- **TimeRange**：时间区间运算，支持重叠检测、包含判断、时点与区间的关系判定。
- **Timebase**：帧率抽象基类，预置常见帧率常量。

### ffmpeg — FFmpeg 封装

- **FFmpeg**：异步 FFmpeg 进程管理器。基于 `pyee` EventEmitter 的事件驱动设计，支持启动、中止与终止操作，自动解析 stderr 输出流，支持编码信息探测。
- **FFmpegError**：带正则匹配的错误分类工厂。子类涵盖文件未找到、参数错误、不支持的编码器、可执行文件缺失、进程运行中冲突等场景。
- **FFmpegCodingInfo**：编码信息值对象，包含编码器、时长、分辨率、比特率等字段。
- **FFmpegFilePathPreprocessor**：路径预处理，处理引号兼容性与 Windows 路径适配。

### filesystem — 文件系统工具

- **PathExpander**：路径展开，支持通配符、环境变量和用户目录（`~`）。
- **CmdFinder**：可执行文件查找，遍历 PATH 并检测有效后缀。
- **SuffixFinder**：文件后缀匹配。
- **PathValidator / SuffixValidator / EmptyDirValidator / ExecutableValidator**：路径验证链组件，支持组合与短路。
- **EncodingDetector**：基于 chardet 的文本编码探测。

### iotools — IO 工具

跨平台的子进程创建（Windows 下自动配置 `CREATE_NEW_PROCESS_GROUP` 以支持信号发送）、流式读写、字节流记录与重定向。

### text — 文本工具

- **TagReplacer**：模板标签替换系统，支持从对象属性、路径信息、环境变量等来源动态渲染文本。
- **auto_quote / auto_unquote**：智能引号添加与去除。
- **random_string**：随机字符串生成。
- **auto_list_text / auto_unwrap**：文本按分隔符拆分与去换行。

### number — 数值工具

- **NumberRange**：带边界的数值范围对象，支持跨区间映射、百分比转换与 clamp 裁剪。
- **quick_clamp / quick_remap**：便捷数值函数，功能类似 AE 表达式中的 clamp 与 remap。

### system — 系统抽象

- **SystemType**：平台枚举，区分 Windows / macOS / Linux / WSL / iOS / Android / FreeBSD。
- **is_user_admin**：跨平台管理员权限检测。
- **opener**：跨平台文件或 URL 打开（`xdg-open` / `open` / `start`）。
- **cross_runner**：跨平台命令执行封装。

### collectiontools — 集合工具

- **flatten_list**：递归展平任意深度的嵌套可迭代对象。
- **iter_with_separator**：在迭代元素间插入分隔符，适用于构建连接清单。
- **split_to_two**：按谓词将序列拆分为两组。

### i18n — 国际化

基于 gettext 的翻译基础设施，提供 `_()` 和 `_ng()`（复数）函数。简体中文为源语言。

## 快速示例

```python
from cx_studio.core import CxTime, FileSize, Timebase

# 时码解析
t = CxTime.from_str("01:23:45:12", rate=Timebase.fps_25)
print(t.total_frames)  # 124587

# 文件大小
fs = FileSize.from_bytes(1_234_567_890)
print(fs.pretty_string())  # "1.15 GiB" (binary)
print(fs.pretty_string(standard="international"))  # "1.23 GB"
```

```python
from cx_studio.ffmpeg import FFmpeg

async def transcode():
    ff = FFmpeg(executable="/usr/bin/ffmpeg")
    await ff.run(["-i", "input.mp4", "output.avi"])
```

## 链接

返回项目首页：[cx-studio-tk](../..)
