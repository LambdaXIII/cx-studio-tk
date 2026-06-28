# cx-studio-tk

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

[![PyPI - Version](https://img.shields.io/pypi/v/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cx-studio-tk)](https://pypi.org/project/cx-studio-tk/)
[![License](https://img.shields.io/github/license/LambdaXIII/cx-studio-tk)](LICENSE)

A Python toolkit for film and video post-production.

## Table of Contents

- [Packages](#packages)
- [Tools](#tools)
- [Installation](#installation)
- [Internationalization & Translation](#internationalization--translation)
- [Building from Source](#building-from-source)
- [Contributing](#contributing)
- [License](#license)

## Packages

Three independently distributable packages, listed in dependency-chain order:

### [cx-studio](packages/cx-studio/README.md)  |  [PyPI](https://pypi.org/project/cx-studio/)

Infrastructure library providing common components for post-production tool development. Includes timecode (CxTime), file size (FileSize), FFmpeg async wrapper, filesystem utilities, text template rendering (TagReplacer), value mapping, cross-platform system abstractions, and internationalization infrastructure. Can be installed and used independently.

### [cx-wealth](packages/cx-wealth/README.md)  |  [PyPI](https://pypi.org/project/cx-wealth/)

A Rich-based terminal UI component library. Provides a declarative help system DSL (WealthHelp), composable label rendering (WealthLabel), object detail panels (WealthDetail), adaptive multi-column layouts (DynamicColumns), index lists, and other extensions. Depends on cx-studio.

### [cxalio-studio-tools](packages/cxalio-studio-tools/README.md)  |  [PyPI](https://pypi.org/project/cxalio-studio-tools/)

5 ready-to-use CLI tools — Media Scout, Media Killer, FFpretty, Jpegger, HostsKeeper — along with a general-purpose CLI application framework (cx_tools.app). Depends on cx-studio and cx-wealth.

## Tools

### Media Scout | `mediascout`

Extracts source media paths from post-production project files and outputs them to stdout.

Supported formats:
- Final Cut Pro 7 XML (`.xml`)
- Final Cut Pro X / 11 FCPXML (`.fcpxml` / `.fcpxmld`)
- Edit Decision List EDL (`.edl`)
- DaVinci Resolve metadata tables (`.csv`)
- Plain text file listings (`.txt`)

Usage:

```shell
mediascout "project.fcpxml" > sources.txt
```

→ [Media Scout Help](packages/cxalio-studio-tools/media_scout/help.md)

### Media Killer | `mediakiller`

A preset-driven ffmpeg batch transcoding tool. Defines transcoding parameters (codec, resolution, bitrate, filters, etc.) via TOML preset files. Automatically scans directories recursively, matches file types, and executes the transcoding queue.

Usage:

```shell
mediakiller "preset.toml" "source.mp4" "source_dir/"
```

→ [Media Killer Help](packages/cxalio-studio-tools/media_killer/help.md)

### FFpretty | `ffpretty`

A simple ffmpeg command-line wrapper. Passes all arguments through to ffmpeg, provides a Rich progress bar, and suppresses ffmpeg's native output.

```shell
ffpretty -i input.mp4 -c:v libx264 output.mp4
```

### Jpegger | `jpegger`

A batch image processing tool. Supports color space conversion, proportional scaling, and multi-format output (JPEG / PNG / WebP, etc.).

```shell
jpegger input_dir/ output_dir/ --format webp --scale 50%
```

### HostsKeeper | `hostskeeper`

A hosts file manager. Fetches hosts content from multiple sources (local files, remote URLs), merges and deduplicates, then writes to the system hosts file. Supports rule-driven filtering and auto-updating, with automatic DNS cache flushing (Windows / macOS).

> HostsKeeper requires administrator privileges to run.

→ [HostsKeeper Help](packages/cxalio-studio-tools/hosts_keeper/help.md)

## Installation

```shell
# Install everything (all tools included)
pip install cx-studio-tk

# Install individual packages
pip install cx-studio             # infrastructure library only
pip install cx-wealth             # UI component library only
pip install cxalio-studio-tools   # CLI tools only
```

Using pipx for the tools package is recommended:

```shell
pipx install cxalio-studio-tools
```

Requires Python >= 3.12, < 3.15.

## Internationalization & Translation

This project uses **gettext + Babel** for internationalization. Each distributable package maintains its own translation files under its source directory:

| Package | Translation File Location | Domain |
|---|---|---|
| cx-studio | `cx_studio/locales/` | `cx-studio` |
| cx-wealth | `cx_wealth/locales/` | `cx-wealth` |
| cxalio-studio-tools | `cx_tools/locales/` | `cx-tools` |

> **Source Language Policy**: The standard language for this project is Simplified Chinese (zh_CN). `_()` calls in the code use Chinese as msgid, with translations (including English) provided via `.po` `msgstr` entries. Designs using English as the source language are not accepted.

### Quick Start for Translators

1. Locate the `.po` file for the package you want to translate, e.g. `cx_tools/locales/en_US/LC_MESSAGES/cx-tools.po`
2. Open it with **Poedit** (recommended) or any text editor, fill `msgstr ""` with your target language
3. Save and submit a Pull Request

You can verify that the `.po` compiles correctly to `.mo` using the full command (e.g. `uv run pybabel compile --domain cx-tools --directory cx_tools/locales`, executed in the corresponding package directory).

### Workflow for Developers

Wrap user-facing strings with `_()` in code:

```python
from cx_studio.i18n import _   # inside cx-studio package
from cx_wealth.i18n import _   # inside cx-wealth package
from cx_tools.i18n import _    # inside cxalio-studio-tools package

appenv.say(_("程序正常退出。"))

# Strings with variables — variables go outside _()
appenv.say(_("已处理 {count} 个文件。").format(count=n))

# Plural forms
from cx_wealth.i18n import _ng
appenv.say(_ng("找到 {n} 个结果", "找到 {n} 个结果", n).format(n=n))
```

Rules:
- Only wrap **user-facing fixed text** — not variables, file paths, or command-line argument names
- Rich markup tags (`[cx.error]`, `[green]`) stay outside, never inside `_()`
- After adding new strings, run the extraction command to update the `.po` template

Extract-Translate-Compile cycle (run in the corresponding package directory):

```shell
# cx-studio (run in packages/cx-studio/)
uv run pybabel extract --mapping babel.cfg --output-file cx_studio/locales/cx-studio.pot --project cx-studio --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-studio --input-file cx_studio/locales/cx-studio.pot --output-dir cx_studio/locales
uv run pybabel compile --domain cx-studio --directory cx_studio/locales

# cx-wealth (run in packages/cx-wealth/)
uv run pybabel extract --mapping babel.cfg --output-file cx_wealth/locales/cx-wealth.pot --project cx-wealth --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-wealth --input-file cx_wealth/locales/cx-wealth.pot --output-dir cx_wealth/locales
uv run pybabel compile --domain cx-wealth --directory cx_wealth/locales

# cxalio-studio-tools (run in packages/cxalio-studio-tools/)
uv run pybabel extract --mapping babel.cfg --output-file cx_tools/locales/cx-tools.pot --project 'cxalio-studio-tools' --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-tools --input-file cx_tools/locales/cx-tools.pot --output-dir cx_tools/locales
uv run pybabel compile --domain cx-tools --directory cx_tools/locales
```

### Help Text (help.md)

Help text uses filename suffixes to distinguish languages:

```
help.md            # Chinese (source language)
help.en_US.md      # English
```

Help text contains no `_()` calls. Translators simply copy `help.md` to `help.<locale>.md` and translate section by section.

## Building from Source

```shell
git clone git@github.com:LambdaXIII/cx-studio-tk.git
cd cx-studio-tk
uv sync
```

## Contributing

Issues and Pull Requests are welcome. Before submitting a PR, please ensure:

- Format code by running `uv run black .` in the project root
- Add docstrings for new public functions and classes
- Follow the code conventions described in AGENTS.md

## License

This program collection is released under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) open source license, with the following additional terms:

### Additional Terms (pursuant to GPLv3, section 7)

1. When you distribute modified versions of this program, you must modify the program's name or version number in a reasonable way to distinguish it from the original version. (Per [GPLv3, 7(c)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L372-L374))

2. You may not remove the copyright notices displayed by this program. (Per [GPLv3, 7(b)](https://github.com/HMCL-dev/HMCL/blob/11820e31a85d8989e41d97476712b07e7094b190/LICENSE#L368-L370))
