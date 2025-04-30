# Cxalio Studio Tools

## 简介

包含是一系列用于影视后期制作的小工具：

- [Media Killer](media_killer/help.md)
  根据配置文件操纵 ffmpeg 快速转吗

- [Media Scout](media_scout/help.md)
  从常见的工程文件中读取原素材路径

## 安装方法

使用 pip 安装即可：

```shell
pip install cxalio-studio-tools
# 建议使用pipx安装
pipx install cxalio-studio-tools
```

## 各个小工具

### Media Killer

[Media Killer](media_killer/help.md) 通过解析预设文件，为媒体文件创建转码任务，
并调用 ffmpeg 执行。

通过 `-g|--generate` 参数可以生成预设文件模板。

```shell
mediakiller -g "新的预设.toml"
```

预设文件模板中包含详细的说明，**请一定在修改之后再使用它** 。

使用时，
直接在命令之后指定多个预设文件和需要转码的文件（或者文件夹）即可：

```shell
mediakiller "预设1.toml" "预设2.toml" "媒体文件1.mp4" "媒体文件2.mov"  "媒体文件夹/" ...
```

mediakiller 将会自动识别预设文件，并对源文件路径进行展开和搜索。

此工具的具体介绍在[这里](media_killer/help.md)。

### Media Scout

[Media Scout](media_scout/help.md) 会分析常见的工程文件，并从中解析原素材路径。
默认情况下输出的路径将会直接输出到 stdout，
这样你就可以方便地重定向输出的内容了。

目前支持解析的文件包括：

- 经典 XML 项目文件 (Final Cut Pro 7 XML) `.xml`
- FCPXML 项目文件（Final Cut Pro X|11 XML）`.fcpxml` 或 `.fcpxmld`
- 剪辑决定表（Editing Decision List）`.edl`
- Davinci Resolve 元数据表格 `.csv`
- 纯文本文件列表 `.txt`

输入 `mediascout -h` 可查看详细选项的说明。
详细信息请看 [这里](media_scout/help.md)。

> Media Killer 依赖于 Media Scout 中的工程文件探测功能。

### FFpretty

FFpretty 是一个简单的 ffmpeg 包装。

它直接转发提供的所有参数给 ffmpeg，并提供一个类似于 Media Killer 的进度条。

> 因为 FFpretty 屏蔽了所有来自 ffmpeg 的输出，所以当运行出错时，仍需要手动检查错误。
