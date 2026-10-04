# subtitler User Guide

> *Subtitle format conversion — move it, don't edit it.*

## Intro

subtitler converts a subtitle file from one format to another. It only moves the model: it reads every subtitle item, organizes them by time, and writes them out in the target format — it does not rewrite text, trim times, or reorder content. Fields the source format cannot express stay empty and are never invented.

```bash
subtitler movie.srt movie.ttml
```

## Basic Usage

```
subtitler INPUT OUTPUT
```

| Argument | Meaning |
|---|---|
| `INPUT` | Input subtitle file; the format is recognized by extension |
| `OUTPUT` | Output subtitle file; the format is recognized by extension |

- Source and target may use the same format (round-trip conversion);
- An unrecognized extension aborts with an error and produces no output.

## Supported Formats

| Format | Extensions |
|---|---|
| SubRip (SRT) | `.srt` |
| TTML | `.ttml` / `.xml` / `.dfxp` |
| CSV | `.csv` |

All three can serve as source and target and can be converted in any direction; multi-line dialogue keeps equivalent line breaks across formats.

## Output Files

Normally a single output file is produced, at the `OUTPUT` path. When the source contains overlapping items and the target format does not allow overlap (see the next section), the output is split into multiple files named "target filename + `.part<k>`" (k starting at 1, in output order), with directory and extension following `OUTPUT`:

```bash
subtitler movie.ttml movie.srt   # overlapping source → movie.part1.srt, movie.part2.srt ...
```

Before writing, every target path is checked at once: if any target (including derived `.part<k>` paths) already exists, the tool aborts with an error, writes no file, and never overwrites an existing file.

## Overlap and Splitting

- Overlap (two subtitle time ranges partially coinciding) is a legal state in the model;
- When exporting to a format that allows overlap (TTML / CSV), it is preserved as-is and a single file is produced;
- When exporting to a format that does not allow overlap (SRT), the output is split automatically: items are scanned and grouped by time so that no group overlaps and no item is dropped; grouping does not aim for the fewest files but is guaranteed legal;
- Touching endpoints (e.g. `[0,5s]` and `[5,10s]`) do not count as overlap and never cause a split.

## CSV Header Contract

There is no general standard for subtitle CSV, so this tool defines its own header contract: the reserved columns must appear first, in order.

```
start,end,text,speaker
```

| Column | Meaning |
|---|---|
| `start` / `end` | Start and end times as millisecond-precision `HH:MM:SS.mmm` |
| `text` | Subtitle text; multi-line dialogue uses RFC 4180 newlines inside quotes |
| `speaker` | Speaker; an empty cell means no speaker |
| Other columns | Extension columns whose names are the item's extension keys, mapped as-is; export uses the union of extension keys across all items, filling missing cells empty |

A malformed header, a bad time literal, or an extension column colliding with a reserved column aborts with an error.

## Getting Help

```bash
subtitler -h            # grouped help
subtitler --tutorial    # this tutorial
```

> *Project: https://github.com/LambdaXIII/cx-studio-tk*
