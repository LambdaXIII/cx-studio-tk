# Jpegger

Jpegger is a simple command-line tool for batch image conversion.

It is built on Pillow and can quickly convert image formats, resize, change color space, and adjust quality.

## Usage

Use it directly:

```shell
jpegger "image1.jpg" "image2.png" "image3.bmp" ...
```

By default, jpegger converts input images to the commonly used JPEG format and outputs them to the current directory.

You can also specify an output directory:

```shell
jpegger "image1.jpg" "image2.png" -o "output_dir"
```

## Output Format

Use the `-f|--format` option to specify the output format:

```shell
jpegger "image.png" -f jpg
jpegger "image.jpg" -f png
```

Most common formats readable and writable by Pillow are supported. The default output format is JPEG if not specified.

## Size Control

Jpegger provides three mutually exclusive ways to control output size, in order of priority from high to low:

1. `--scale FACTOR`: Scale the image proportionally.
2. `-s|--size WIDTHxHEIGHT`: Specify the target dimensions.
3. `--width WIDTH` / `--height HEIGHT`: Specify only width or height.

When multiple methods are specified at the same time, only the highest-priority one takes effect, and lower-priority options are ignored.

### `--scale`

Scale the image proportionally by the given factor.

```shell
jpegger "image.jpg" --scale 0.5
jpegger "image.jpg" --scale 2
```

### `-s|--size`

Specify the target dimensions in the format `WIDTHxHEIGHT`.

```shell
jpegger "image.jpg" -s 1920x1080
jpegger "image.jpg" --size 800x600
```

### `--width` and `--height`

When only width or height is specified, the other dimension is automatically calculated based on the original aspect ratio.

```shell
jpegger "image.jpg" --width 1920
jpegger "image.jpg" --height 1080
```

## Color Space

Use the `-c|--color-space` option to convert the color space:

```shell
jpegger "image.png" -c RGB
jpegger "image.jpg" -c L
jpegger "image.jpg" -c CMYK
```

Available values are `RGB`, `L` (grayscale), and `CMYK`.

## Encoding Quality

Use the `-q|--quality` option to set the output quality. The typical range is 1 to 95.

```shell
jpegger "image.png" -q 90
jpegger "image.png" -q 75
```

If not specified, the built-in commonly used quality setting is used.

## Other Options

### `-o|--output`

Specify the output directory. Defaults to the current working directory.

### `-y|--force-overwrite`

Force overwriting existing target files. When not set, jpegger will automatically rename files with conflicting names.

### `-d|--debug`

Enable debug mode to output more internal information.

### `-h|--help`

Show brief help information.

### `--tutorial` / `--full-help`

Show the full tutorial document (this document).

## Practical Examples

### Batch convert PNG to JPEG

```shell
jpegger "*.png"
```

### Scale down by half and save to a specific directory

```shell
jpegger "image.jpg" --scale 0.5 -o "thumbnails"
```

### Convert to grayscale

```shell
jpegger "image.jpg" -c L
```

### Specify high-quality output

```shell
jpegger "source.png" -f jpg -q 95
```
