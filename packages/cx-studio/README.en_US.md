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
- **FileSize**: Typed representation of file size, supporting both binary (KiB/MiB/GiB) and international (KB/MB/GB) standards, with `pretty_string()` for human-readable output.
- **TimeRange**: Time range operations, supporting overlap detection, containment checks, and relationship determination between time points and ranges.
- **Timebase**: Frame rate abstraction (fps + drop_frame), with a `from_fps()` factory to construct from a frame rate.

### ffmpeg — FFmpeg Wrapper

- **FFmpegCodingInfo**: Encoding information value object containing fields such as codec, duration, resolution, and bitrate.
- **FFmpegFilePathPreprocessor**: Path preprocessing for quote compatibility and Windows path adaptation.

### filesystem — File System Utilities

- **PathExpander**: Path expansion supporting wildcards, environment variables, and user directories (`~`).
- **CmdFinder**: Executable file lookup, traversing PATH and detecting valid suffixes.
- **SuffixFinder**: File suffix matching.
- **PathValidator / SuffixValidator / EmptyDirValidator / ExecutableValidator**: Path validation chain components, supporting composition and short-circuit evaluation.
- **EncodingDetector**: Text encoding detection based on chardet.

### iotools — IO Utilities

Cross-platform subprocess creation (automatically configures `CREATE_NEW_PROCESS_GROUP` on Windows for signal support), streaming read/write, byte stream recording and redirection.

### text — Text Utilities

- **TagReplacer**: Template tag replacement system supporting dynamic text rendering from object properties, path information, environment variables, and other sources.
- **auto_quote / auto_unquote**: Intelligent quote addition and removal.
- **random_string**: Random string generation.
- **auto_list_text / auto_unwrap**: Text splitting by delimiter and unwrapping newlines.

### number — Numeric Utilities

- **NumberRange**: Bounded numeric range object supporting cross-range mapping, percentage conversion, and clamp clipping.
- **quick_clamp / quick_remap**: Convenient numeric functions similar to clamp and remap in After Effects expressions.

### system — System Abstraction

- **SystemType**: Platform enumeration distinguishing Windows / macOS / Linux / WSL / iOS / Android / FreeBSD.
- **is_user_admin**: Cross-platform administrator privilege detection.
- **opener**: Cross-platform file or URL opener (`xdg-open` / `open` / `start`).
- **cross_runner**: Cross-platform command execution wrapper.

### collectiontools — Collection Utilities

- **flatten_list**: Recursively flatten arbitrarily nested iterable objects.
- **iter_with_separator**: Insert separators between iteration elements, useful for building concatenated lists.
- **split_to_two**: Split a sequence into two groups by predicate.

### i18n — Internationalization

Gettext-based translation infrastructure providing `_()` and `_ng()` (plural) functions. Simplified Chinese is the source language.

## Links

Back to project home: [cx-studio-tk](../..)
