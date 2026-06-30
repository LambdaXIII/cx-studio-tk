# Jpegger

Jpegger 是一个简单的批量图片转换命令行工具。

它基于 Pillow 实现，可以快速对图片进行格式转换、尺寸缩放、色彩空间转换以及质量调整。

## 基本用法

直接使用即可：

```shell
jpegger "图片1.jpg" "图片2.png" "图片3.bmp" ...
```

默认情况下，jpegger 会将输入图片转换为常用的 JPEG 格式并输出到当前目录。

也可以指定输出目录：

```shell
jpegger "图片1.jpg" "图片2.png" -o "输出目录"
```

## 输出格式

使用 `-f|--format` 选项指定输出格式：

```shell
jpegger "图片.png" -f jpg
jpegger "图片.jpg" -f png
```

支持 Pillow 可读写的大部分常见格式。不指定时默认输出为 JPEG。

## 尺寸控制

Jpegger 提供三种互斥的尺寸控制方式，按优先级从高到低依次为：

1. `--scale FACTOR`：按比例缩放图片。
2. `-s|--size WIDTHxHEIGHT`：指定目标尺寸。
3. `--width WIDTH` / `--height HEIGHT`：单独指定宽度或高度。

当同时指定多种方式时，只有优先级最高的一项会生效，较低优先级的选项会被忽略。

### `--scale`

按给定因子等比例缩放图片。

```shell
jpegger "图片.jpg" --scale 0.5
jpegger "图片.jpg" --scale 2
```

### `-s|--size`

指定目标尺寸，格式为 `WIDTHxHEIGHT`。

```shell
jpegger "图片.jpg" -s 1920x1080
jpegger "图片.jpg" --size 800x600
```

### `--width` 与 `--height`

只指定宽度或高度时，另一个维度会按原始比例自动计算。

```shell
jpegger "图片.jpg" --width 1920
jpegger "图片.jpg" --height 1080
```

## 色彩空间

使用 `-c|--color-space` 选项转换色彩空间：

```shell
jpegger "图片.png" -c RGB
jpegger "图片.jpg" -c L
jpegger "图片.jpg" -c CMYK
```

可选值为 `RGB`、`L`（灰度）和 `CMYK`。

## 编码质量

使用 `-q|--quality` 选项设置输出质量，取值范围通常为 1 到 95。

```shell
jpegger "图片.png" -q 90
jpegger "图片.png" -q 75
```

不指定时使用内置的常用质量设置。

## 其它选项

### `-o|--output`

指定输出目录，默认为当前工作目录。

### `-y|--force-overwrite`

强制覆盖已存在的目标文件。未指定时，jpegger 会自动对重名文件进行重命名。

### `-d|--debug`

开启调试模式，输出更多内部信息。

### `-h|--help`

显示简要帮助信息。

### `--tutorial` / `--full-help`

显示完整的教程文档（即本文档）。

## 实战示例

### 将 PNG 批量转换为 JPEG

```shell
jpegger "*.png"
```

### 等比例缩小一半并保存到指定目录

```shell
jpegger "图片.jpg" --scale 0.5 -o "缩略图"
```

### 转换为灰度图

```shell
jpegger "图片.jpg" -c L
```

### 指定高质量输出

```shell
jpegger "原图.png" -f jpg -q 95
```
