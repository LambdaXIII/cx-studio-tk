# Cxalio Studio Tools

包含 5 个命令行工具和一个通用的 CLI 应用框架。

## 工具

### Media Killer

[Media Killer](media_killer/help.md) 通过解析 TOML 预设文件，为媒体文件创建批量转码任务，并调用 ffmpeg 执行。

通过 `-g|--generate` 参数可以生成预设文件模板：

```shell
mediakiller -g "新的预设.toml"
```

使用时，在命令之后指定多个预设文件和需要转码的文件（或文件夹）：

```shell
mediakiller "预设1.toml" "预设2.toml" "媒体文件1.mp4" "媒体文件2.mov" "媒体文件夹/" ...
```

mediakiller 会自动识别预设文件并对源文件路径进行展开和递归搜索。

详细信息参见 [Media Killer 帮助文档](media_killer/help.md)。

### Media Scout

[Media Scout](media_scout/help.md) 分析常见的影视后期工程文件，从中提取原始素材路径。输出到 stdout，方便重定向。

目前支持解析的格式：

- 经典 XML 项目文件（Final Cut Pro 7 XML）`.xml`
- FCPXML 项目文件（Final Cut Pro X / 11 XML）`.fcpxml` / `.fcpxmld`
- 剪辑决定表（EDL）`.edl`
- DaVinci Resolve 元数据表格 `.csv`
- 纯文本文件列表 `.txt`

```shell
mediascout "project.fcpxml" > sources.txt
```

输入 `mediascout -h` 查看详细选项。详细信息参见 [Media Scout 帮助文档](media_scout/help.md)。

> Media Killer 依赖于 Media Scout 中的工程文件探测功能。

### FFpretty

FFpretty 是一个简单的 ffmpeg 包装。它直接透传所有参数给 ffmpeg，并提供 Rich 进度条显示。

```shell
ffpretty -i input.mp4 -c:v libx264 output.mp4
```

> FFpretty 屏蔽了所有来自 ffmpeg 的输出；出错时需手动检查 ffmpeg 的错误信息。

### Jpegger

Jpegger 是一个批量图片处理工具。支持色彩空间转换、按比例缩放、多格式输出（JPEG / PNG / WebP 等）。

```shell
jpegger input_dir/ output_dir/ --format webp --scale 50%
```

### HostsKeeper

[HostsKeeper](hosts_keeper/help.md) 是一个 hosts 文件管理工具。它从多个来源获取 hosts 内容（本地文件、远程 URL），合并去重后写入系统 hosts 文件。支持按规则筛选内容与自动更新，并自动刷新 DNS 缓存（Windows / macOS）。

> HostsKeeper 需要管理员权限才能修改 hosts 文件。

详细信息参见 [HostsKeeper 帮助文档](hosts_keeper/help.md)。

## 应用框架

所有工具均构建在 `cx_tools.app` 应用框架之上，该框架提供统一的 CLI 应用生命周期管理：

- **IApplication** — 应用生命周期接口（`start` → `run` → `stop`）
- **IAppEnvironment** — 运行环境抽象，提供 Rich console、SIGINT 处理、`say()` / `whisper()` 分级输出、管理员权限检测
- **SafeError** — 统一异常处理，Rich 样式展示可恢复的应用错误
- **AppContext** — 统一参数解析模式（`from_arguments()` 工厂方法）

## 安装

```shell
pip install cxalio-studio-tools
# 建议使用 pipx 独立安装
pipx install cxalio-studio-tools
```

要求 Python >= 3.12, < 3.15。

## 链接

返回项目首页：[cx-studio-tk](../..)
