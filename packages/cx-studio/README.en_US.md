# cx-studio

**语言 / Languages**: [中文](README.md) | [English](README.en_US.md)

Infrastructure library providing common components for film and TV post-production automation tools.

## Installation

```bash
pip install cx-studio
```

Requires Python >= 3.12, < 3.15.

## Modules

### core — Core Value Objects

- **CxTime**: SMPTE timecode parsing and calculation, supporting common frame rates such as 23.976 / 24 / 25 / 29.97 / 30 / 50 / 59.94 / 60 fps.
- **Timebase**: Frame rate abstraction (fps + drop_frame), with a `from_fps()` factory to construct from a frame rate.
- **TimeRange**: Time range operations, supporting overlap detection, containment checks, and relationship determination between time points and ranges.
- **FileSize**: Typed representation of file size, supporting both binary (KiB/MiB/GiB) and international (KB/MB/GB) standards, with `pretty_string()` for human-readable output.
- **NumberRange**: Bounded numeric range object supporting cross-range mapping, percentage conversion, and clamp clipping.
- **quick_clamp / quick_remap**: Convenient numeric functions similar to clamp and remap in After Effects expressions.
- **flatten_list / iter_with_separator / split_to_two**: Collection utilities — recursive flattening, inserting separators between iteration elements, and splitting a sequence by predicate.

### text — Text Utilities

- **TagReplacer**: Template tag replacement system supporting dynamic text rendering from object properties, path information, environment variables, and other sources (with `PathInfoProvider`).
- **auto_quote / auto_unquote / auto_list_text / auto_unwrap**: Smart quote add/remove, text splitting by delimiter and unwrapping newlines.
- **random_string**: Random string generation.
- **escape_arg / join_args**: Command-line argument escaping and joining.

### filesystem — File System Utilities

- **PathUtils**: Path utility namespace (normalization, suffix handling, quoting, parent/basename extraction, etc.).
- **PathExpander**: Path expansion supporting wildcards, environment variables, and user directories (`~`).
- **CmdFinder**: Executable file lookup, traversing PATH and detecting valid suffixes.
- **SuffixFinder**: File suffix matching.
- **FileList / FileSizer / FileInfoCache**: File list, size calculation, and info caching.
- **detect_file_encoding**: Text encoding detection based on chardet.

### system — System Abstraction

- **SystemType**: Platform enumeration distinguishing Windows / macOS / Linux / WSL / iOS / Android / FreeBSD.
- **CrossRunner**: Cross-platform command execution wrapper.
- **system_open**: Cross-platform file or URL opener (`xdg-open` / `open` / `start`).
- **is_user_admin**: Cross-platform administrator privilege detection.

### process — Subprocess & Streams

Cross-platform subprocess creation (automatically configures `CREATE_NEW_PROCESS_GROUP` on Windows for signal support), streaming read/write, byte stream recording and redirection. Provides both synchronous (`StreamUtils`) and asynchronous (`AsyncStreamUtils`) interfaces.

### clikit — CLI Infrastructure

- **DoubleTrigger**: CLI double-trigger component, working with the `FIRST_TRIGGERED` / `SECOND_TRIGGERED` state constants to implement double-press detection.

### ffmpeg — FFmpeg Wrapper

- **FFmpegAsync**: Asynchronous FFmpeg executor.
- **FFmpegCodingInfo / FFmpegProcessInfo / FFmpegFormatInfo**: Encoding info, process info, and format info value objects.
- **FFmpegArgumentsPreProcessor**: Argument preprocessing for quote compatibility and Windows path adaptation.

### i18n — Internationalization

Gettext-based translation infrastructure providing `_()` and `_ng()` (plural) functions, plus `detect_locale()` (locale detection) and `load_localized_text()` (localized text loader). Simplified Chinese is the source language.

## Links

Back to project home: [cx-studio-tk](../..)
