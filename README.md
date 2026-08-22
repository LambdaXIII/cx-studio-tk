# cx-studio-tk

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

[![PyPI - Version](https://img.shields.io/pypi/v/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![License](https://img.shields.io/github/license/LambdaXIII/cx-studio-tk)](LICENSE)

**影视后期，硬核一点。**

一套用 Python 实现的工具包：素材定位、ffmpeg 批量转码、图片批处理、hosts 管理。每个功能独立开放——预设流程不适配你的工作台？自由拼装，快速搭出你自己的后期流水线。

## 目录

- [包与安装](#包与安装)
- [工具](#工具)
- [贡献](#贡献)
- [开源协议](#开源协议)

## 包与安装

三个可独立分发的包，按依赖链顺序排列：

| 包 | 说明 | 安装 |
|---|---|---|
| [cx-studio](packages/cx-studio/README.md) | 基础设施库（时间码、FFmpeg 封装、文件系统、文本模板、系统抽象、i18n 等） | `pip install cx-studio` |
| [cx-wealthy](packages/cx-wealthy/README.md) | 基于 Rich 的终端结构化文档与 UI 组件库（标签/详情双渲染协议、声明式帮助系统等） | `pip install cx-wealthy` |
| [cxalio-studio-tools](packages/cxalio-studio-tools/README.md) | 5 个 CLI 工具 + 通用应用框架（cx_tools.app），依赖前两者 | `pip install cxalio-studio-tools` |

安装全部（含所有工具）：

```shell
pip install cx-studio-tk
```

建议使用 pipx 安装工具包：

```shell
pipx install cxalio-studio-tools
```

要求 Python >= 3.12, < 3.15。

## 工具

### Media Scout | `mediascout`

从影视后期工程文件中提取原始素材路径，输出到 stdout。支持 Final Cut Pro 7 XML、FCPXML、EDL、DaVinci Resolve 元数据表格与纯文本文件列表。

```shell
mediascout "project.fcpxml" > sources.txt
```

详情见 [Media Scout 帮助文档](packages/cxalio-studio-tools/media_scout/help.md)。

### Media Killer | `mediakiller`

预设驱动的 ffmpeg 批量转码工具。通过 TOML 预设文件定义转码参数，自动递归扫描目录并执行转码队列。

```shell
mediakiller "preset.toml" "source.mp4" "source_dir/"
```

详情见 [Media Killer 帮助文档](packages/cxalio-studio-tools/media_killer/help.md)。

### FFpretty | `ffpretty`

ffmpeg 简易命令行包装。透传所有参数给 ffmpeg，提供 Rich 进度条显示，屏蔽 ffmpeg 原生输出。

```shell
ffpretty -i input.mp4 -c:v libx264 output.mp4
```

详情见 `ffpretty -h`。

### Jpegger | `jpegger`

批量图片处理工具。支持色彩空间转换、按比例缩放、多格式输出（JPEG / PNG / WebP 等）。

```shell
jpegger input_dir/ output_dir/ --format webp --scale 50%
```

详情见 [Jpegger 帮助文档](packages/cxalio-studio-tools/jpegger/help.md)。

### HostsKeeper | `hostskeeper`

hosts 文件管理器。从多个来源获取 hosts 内容，合并去重后写入系统 hosts 文件，支持规则筛选与自动更新，并自动刷新 DNS 缓存（Windows / macOS）。

hostskeeper update -p   # 先预览将要写入的内容
hostskeeper update      # 确认后执行
```
hostskeeper ...
```

详情见 [HostsKeeper 帮助文档](packages/cxalio-studio-tools/hosts_keeper/help.md)。

## 贡献

欢迎提交 Issue 和 Pull Request。开发流程、代码约定、国际化（i18n）工作流等详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 开源协议

该程序集在 [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) 开源协议下发布，同时附有以下附加条款。

### 附加条款（依据 GPLv3 开源协议第七条）

1. 当你分发该程序的修改版本时，你必须以一种合理的方式修改该程序的名称或版本号，以示其与原始版本不同。（依据 [GPLv3, 7(c)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L372-L374)）

2. 你不得移除该程序所显示的版权声明。（依据 [GPLv3, 7(b)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L368-L370)）
