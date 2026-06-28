# cx-studio-tk

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

[![PyPI - Version](https://img.shields.io/pypi/v/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![License](https://img.shields.io/github/license/LambdaXIII/cx-studio-tk)](LICENSE)

面向影视后期制作的 Python 工具集。

## 目录

- [包](#包)
- [工具](#工具)
- [安装](#安装)
- [国际化与翻译](#国际化与翻译)
- [从源码构建](#从源码构建)
- [贡献指南](#贡献指南)
- [开源协议](#开源协议)

## 包

三个可独立分发的包，按依赖链顺序排列：

### [cx-studio](packages/cx-studio/README.md)  |  [PyPI](https://pypi.org/project/cx-studio/)

基础设施库，为影视后期工具的开发提供通用组件。包含时间时码（CxTime）、文件大小（FileSize）、FFmpeg 异步封装、文件系统工具、文本模板渲染（TagReplacer）、数值映射、跨平台系统抽象、国际化基础设施等模块。可独立安装使用。

### [cx-wealth](packages/cx-wealth/README.md)  |  [PyPI](https://pypi.org/project/cx-wealth/)

基于 Rich 的终端 UI 组件库。提供声明式帮助系统 DSL（WealthHelp）、可组合标签渲染（WealthLabel）、对象详情面板（WealthDetail）、自适应多列布局（DynamicColumns）、索引列表等扩展。依赖 cx-studio。

### [cxalio-studio-tools](packages/cxalio-studio-tools/README.md)  |  [PyPI](https://pypi.org/project/cxalio-studio-tools/)

5 个可直接使用的命令行工具 — Media Scout、Media Killer、FFpretty、Jpegger、HostsKeeper，以及通用的 CLI 应用框架（cx_tools.app）。依赖 cx-studio 和 cx-wealth。

## 工具

### Media Scout | `mediascout`

从影视后期工程文件中提取原始素材路径，输出到 stdout。

支持格式：
- Final Cut Pro 7 XML（`.xml`）
- Final Cut Pro X / 11 FCPXML（`.fcpxml` / `.fcpxmld`）
- 剪辑决定表 EDL（`.edl`）
- DaVinci Resolve 元数据表格（`.csv`）
- 纯文本文件列表（`.txt`）

用法：

```shell
mediascout "project.fcpxml" > sources.txt
```

→ [Media Scout 帮助文档](packages/cxalio-studio-tools/media_scout/help.md)

### Media Killer | `mediakiller`

预设驱动的 ffmpeg 批量转码工具。通过 TOML 预设文件定义转码参数（编码器、分辨率、码率、滤镜等），自动递归扫描目录、匹配文件类型、执行转码队列。

用法：

```shell
mediakiller "preset.toml" "source.mp4" "source_dir/"
```

→ [Media Killer 帮助文档](packages/cxalio-studio-tools/media_killer/help.md)

### FFpretty | `ffpretty`

ffmpeg 简易命令行包装。透传所有参数给 ffmpeg，提供 Rich 进度条显示，屏蔽 ffmpeg 原生输出。

```shell
ffpretty -i input.mp4 -c:v libx264 output.mp4
```

### Jpegger | `jpegger`

批量图片处理工具。支持色彩空间转换、按比例缩放、多格式输出（JPEG / PNG / WebP 等）。

```shell
jpegger input_dir/ output_dir/ --format webp --scale 50%
```

### HostsKeeper | `hostskeeper`

hosts 文件管理器。从多个来源获取 hosts 内容（本地文件、远程 URL），合并去重后写入系统 hosts 文件。支持规则驱动的筛选和自动更新，并自动刷新 DNS 缓存（Windows / macOS）。

> HostsKeeper 需要管理员权限运行。

→ [HostsKeeper 帮助文档](packages/cxalio-studio-tools/hosts_keeper/help.md)

## 安装

```shell
# 安装全部（含所有工具）
pip install cx-studio-tk

# 单独安装某个包
pip install cx-studio             # 仅基础设施库
pip install cx-wealth             # 仅 UI 组件库
pip install cxalio-studio-tools   # 仅 CLI 工具集
```

建议使用 pipx 安装工具包：

```shell
pipx install cxalio-studio-tools
```

要求 Python >= 3.12, < 3.15。

## 国际化与翻译

此项目使用 **gettext + Babel** 进行国际化。每个分发包在包源码目录下维护自己的翻译文件：

| 包 | 翻译文件位置 | Domain |
|---|---|---|
| cx-studio | `cx_studio/locales/` | `cx-studio` |
| cx-wealth | `cx_wealth/locales/` | `cx-wealth` |
| cxalio-studio-tools | `cx_tools/locales/` | `cx-tools` |

> **源语言政策**：本项目的标准语言是简体中文（zh_CN）。代码中 `_()` 调用使用中文作为 msgid，英文等翻译通过 `.po` 的 `msgstr` 提供。不接受以英文为源语言的设计。

### 给翻译者的快速入门

1. 找到想翻译的包的 `.po` 文件，例如 `cx_tools/locales/en_US/LC_MESSAGES/cx-tools.po`
2. 用 **Poedit**（推荐）或任何文本编辑器打开，将 `msgstr ""` 填入目标语言
3. 保存并发送 Pull Request

可用完整命令（如 `uv run pybabel compile --domain cx-tools --directory cx_tools/locales`，在对应包目录执行）验证 `.po` 是否被正确编译为 `.mo`。

### 给开发者的工作流

在代码中用 `_()` 包裹用户面向的字符串：

```python
from cx_studio.i18n import _   # cx-studio 包内
from cx_wealth.i18n import _   # cx-wealth 包内
from cx_tools.i18n import _    # cxalio-studio-tools 包内

appenv.say(_("程序正常退出。"))

# 含变量的字符串——变量在 _() 外面
appenv.say(_("已处理 {count} 个文件。").format(count=n))

# 复数形式
from cx_wealth.i18n import _ng
appenv.say(_ng("找到 {n} 个结果", "找到 {n} 个结果", n).format(n=n))
```

规则：
- 只包裹**用户面向的固定文本**，不包裹变量、文件路径、命令行参数名
- Rich markup 标记（`[cx.error]`、`[green]`）在外面，不进入 `_()`
- 写新字符串后运行提取命令更新 `.po` 模板

提取-翻译-编译周期（在对应包目录执行）：

```shell
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

### 帮助文本（help.md）

帮助文本按文件名后缀区分语言：

```
help.md            # 中文（源语言）
help.en_US.md      # 英文
```

帮助文本中无 `_()` 调用，翻译者直接复制 `help.md` 为 `help.<locale>.md` 后逐段翻译。

## 从源码构建

```shell
git clone git@github.com:LambdaXIII/cx-studio-tk.git
cd cx-studio-tk
uv sync
```

## 贡献指南

欢迎提交 Issue 和 Pull Request。在提交 PR 前请确保：

- 修改后在项目根目录运行 `uv run black .` 格式化代码
- 为新公共函数和类添加 docstring
- 遵守仓库中 AGENTS.md 所描述的代码约定

## 开源协议

该程序集在 [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) 开源协议下发布，同时附有以下附加条款。

### 附加条款（依据 GPLv3 开源协议第七条）

1. 当你分发该程序的修改版本时，你必须以一种合理的方式修改该程序的名称或版本号，以示其与原始版本不同。（依据 [GPLv3, 7(c)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L372-L374)）

2. 你不得移除该程序所显示的版权声明。（依据 [GPLv3, 7(b)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L368-L370)）
