# Cxalio Studio Tools

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

Contains 5 CLI tools and a general-purpose CLI application framework.

## Tools

### Media Killer

[Media Killer](media_killer/help.md) parses TOML preset files, creates batch transcoding tasks for media files, and invokes ffmpeg to execute them.

Use the `-g|--generate` flag to generate a preset file template:

```shell
mediakiller -g "新的预设.toml"
```

When running, specify multiple preset files and the media files (or folders) to transcode after the command:

```shell
mediakiller "预设1.toml" "预设2.toml" "媒体文件1.mp4" "媒体文件2.mov" "媒体文件夹/" ...
```

mediakiller automatically identifies preset files and expands source file paths with recursive search.

See the [Media Killer help document](media_killer/help.md) for details.

### Media Scout

[Media Scout](media_scout/help.md) analyzes common post-production project files and extracts raw source footage paths. Output is sent to stdout for easy redirection.

Currently supported formats:

- Classic XML project files (Final Cut Pro 7 XML) `.xml`
- FCPXML project files (Final Cut Pro X / 11 XML) `.fcpxml` / `.fcpxmld`
- Edit Decision Lists (EDL) `.edl`
- DaVinci Resolve metadata tables `.csv`
- Plain text file lists `.txt`

```shell
mediascout "project.fcpxml" > sources.txt
```

Run `mediascout -h` for detailed options. See the [Media Scout help document](media_scout/help.md) for details.

> Media Killer depends on Media Scout's project file detection capability.

### FFpretty

FFpretty is a simple ffmpeg wrapper. It passes all arguments directly through to ffmpeg and provides a Rich progress bar display.

```shell
ffpretty -i input.mp4 -c:v libx264 output.mp4
```

> FFpretty suppresses all output from ffmpeg; when errors occur, check ffmpeg's error messages manually.

### Jpegger

Jpegger is a batch image processing tool. It supports color space conversion, proportional scaling, and multi-format output (JPEG / PNG / WebP, etc.).

```shell
jpegger input_dir/ output_dir/ --format webp --scale 50%
```

### HostsKeeper

[HostsKeeper](hosts_keeper/help.md) is a hosts file management tool. It fetches hosts content from multiple sources (local files, remote URLs), merges and deduplicates them, then writes to the system hosts file. It supports rule-based content filtering, automatic updates, and automatic DNS cache flushing (Windows / macOS).

> HostsKeeper requires administrator privileges to modify the hosts file.

See the [HostsKeeper help document](hosts_keeper/help.md) for details.

## Application Framework

All tools are built on top of the `cx_tools.app` application framework, which provides unified CLI application lifecycle management:

- **IApplication** — Application lifecycle interface (`start` → `run` → `stop`)
- **IAppEnvironment** — Runtime environment abstraction, providing Rich console, SIGINT handling, `say()` / `whisper()` tiered output, and administrator privilege detection
- **SafeError** — Unified exception handling with Rich-styled display for recoverable application errors
- **AppContext** — Unified argument parsing pattern (`from_arguments()` factory method)

## Installation

```shell
pip install cxalio-studio-tools
# It is recommended to install standalone with pipx
pipx install cxalio-studio-tools
```

Requires Python >= 3.12, < 3.15.

## Links

Back to project homepage: [cx-studio-tk](../..)
