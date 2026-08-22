# cx-studio-tk

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

[![PyPI - Version](https://img.shields.io/pypi/v/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![License](https://img.shields.io/github/license/LambdaXIII/cx-studio-tk)](LICENSE)

**Post-production, hardcore.**

A Python toolkit: footage location, ffmpeg batch transcoding, image batch processing, hosts management. Every feature is independent and open—standard flow doesn't fit your pipeline? Snap them together and build a post-production line that's yours.

## Table of Contents

- [Packages & Installation](#packages--installation)
- [Tools](#tools)
- [Contributing](#contributing)
- [License](#license)

## Packages & Installation

Three independently distributable packages, listed in dependency-chain order:

| Package | Description | Install |
|---|---|---|
| [cx-studio](packages/cx-studio/README.md) | Infrastructure library (timecode, FFmpeg wrapper, filesystem, text templates, system abstractions, i18n, etc.) | `pip install cx-studio` |
| [cx-wealthy](packages/cx-wealthy/README.md) | Rich-based terminal document & UI component library (label/detail dual rendering protocols, declarative help system, etc.) | `pip install cx-wealthy` |
| [cxalio-studio-tools](packages/cxalio-studio-tools/README.md) | 5 CLI tools + general-purpose app framework (cx_tools.app), depends on the above two | `pip install cxalio-studio-tools` |

To install everything (all tools included):

```shell
pip install cx-studio-tk
```

Using pipx for the tools package is recommended:

```shell
pipx install cxalio-studio-tools
```

Requires Python >= 3.12, < 3.15.

## Tools

### Media Scout | `mediascout`

Extracts source media paths from post-production project files and outputs them to stdout. Supports Final Cut Pro 7 XML, FCPXML, EDL, DaVinci Resolve metadata tables, and plain-text file listings.

```shell
mediascout "project.fcpxml" > sources.txt
```

See the [Media Scout help](packages/cxalio-studio-tools/media_scout/help.md) for details.

### Media Killer | `mediakiller`

A preset-driven ffmpeg batch transcoding tool. Defines transcoding parameters via TOML preset files, automatically scans directories recursively, and executes the transcoding queue.

```shell
mediakiller "preset.toml" "source.mp4" "source_dir/"
```

See the [Media Killer help](packages/cxalio-studio-tools/media_killer/help.md) for details.

### FFpretty | `ffpretty`

A simple ffmpeg command-line wrapper. Passes all arguments through to ffmpeg, provides a Rich progress bar, and suppresses ffmpeg's native output.

```shell
ffpretty -i input.mp4 -c:v libx264 output.mp4
```

See `ffpretty -h` for details.

### Jpegger | `jpegger`

A batch image processing tool. Supports color space conversion, proportional scaling, and multi-format output (JPEG / PNG / WebP, etc.).

```shell
jpegger input_dir/ output_dir/ --format webp --scale 50%
```

See the [Jpegger help](packages/cxalio-studio-tools/jpegger/help.md) for details.

### HostsKeeper | `hostskeeper`

A hosts file manager. Fetches hosts content from multiple sources, merges and deduplicates them, then writes to the system hosts file. Supports rule-based filtering and auto-updating, with automatic DNS cache flushing (Windows / macOS).

> HostsKeeper requires administrator privileges to run.

```shell
hostskeeper update -p   # preview what will be written
hostskeeper update      # execute after confirmation
```

See the [HostsKeeper help](packages/cxalio-studio-tools/hosts_keeper/help.md) for details.

## Contributing

Issues and Pull Requests are welcome. Development workflow, code conventions, and internationalization (i18n) guidance are documented in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This program collection is released under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) open source license, with the following additional terms:

### Additional Terms (pursuant to GPLv3, section 7)

1. When you distribute modified versions of this program, you must modify the program's name or version number in a reasonable way to distinguish it from the original version. (Per [GPLv3, 7(c)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L372-L374))

2. You may not remove the copyright notices displayed by this program. (Per [GPLv3, 7(b)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L368-L370))
