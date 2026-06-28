# Media Killer

MediaKiller is a command-line tool for quickly deleting media files.

Its basic workflow is very simple:
After entering the command, drag in multiple `preset files` and multiple `source files`, then press Enter to start execution.

But beyond this simple usage, there are rich details:

## Source Files

In MediaKiller, `source files` are not necessarily files that need transcoding.
MediaKiller will automatically probe for possible original files based on the provided source file paths.
The following rules generally apply (where `source file path` refers to the path the user directly provides):

1. If the `source file path` is one of the following types, it will be directly read and expanded to include the file paths contained within:

    - EDL Edit Decision List (.edl)
    - Fcp7XML classic XML timeline file (.xml)
    - Final Cut Pro XML project file (.fcpxml | .fcpxmld)
    - Davinci Resolve exported media metadata (.csv)
    - Plain text files containing paths (including script files) (.txt | .sh)

2. If the `source file path` is a *folder*, all files and subdirectories within it will be expanded recursively.
3. All detected files will be filtered according to the presets in the corresponding `preset file`.

> The project file parsing functionality is implemented by another tool in the toolkit — `MediaScout`.

You can input multiple preset files at once, and MediaKiller will generate transcoding tasks separately and execute them uniformly.

> In short, just add all the preset files, source files, or folders containing source files!

## Preset Files

A preset file is a TOML-format text file containing a description of the transcoding task.

It is not recommended to manually write preset files from scratch; instead, use the `-g` option to generate example preset files and then modify them.

```bash
mediakiller -g example.toml
mediakiller --generate example1.toml example2.toml
```

Although it's not particularly meaningful, you can create multiple preset files at once.

The value of `preset files` lies in their reusability,
so it is recommended to thoroughly test each new preset file and save it properly for long-term use.

> The example preset files contain detailed descriptions, so this document will not explain each parameter in the preset files in detail.

### Field References in Preset Files

Preset files support referencing information using the `${tag}` syntax. Some information can be further customized using parameters.
Here is an overview:

- `${source}` References the source file information of the current task. By default, returns the absolute path of the source file.

| Parameter            | Description                         |
|----------------------|-------------------------------------|
| ${source:fullpath}   | Absolute path of the source file    |
| ${source:parent}     | Parent directory of the source file |
| ${source:name}       | File name of the source file (without path) |
| ${source:basename}   | Base name of the source file (without extension) |
| ${source:suffix}     | Extension of the source file (including the dot) |

- `${target}` References the default target filename, which is calculated from the source file and the settings in the `[target]` section. Its options are the same as `source`.

- `${sep}` Represents the path separator for the current operating system — a backslash on Windows and a forward slash on other systems.

- `${custom:}` Directly references custom fields in the `[custom]` section.

- `${preset:}` References basic information from the configuration file.

> It is highly recommended to use the `--debug --pretend` options when experimenting with these tags.

## Other Details

MediaKiller essentially operates ffmpeg in the background for transcoding, so ffmpeg needs to be installed in advance,
and its path must be specified in the configuration file.

The `--jobs` option specifies how many processes to use for parallel task execution.
However, multimedia transcoding is a compute-intensive task, so too many processes may actually reduce efficiency.
If you do not know what you are doing, please do not abuse this feature.

The `--save-script` (`-s`) option specifies an output file.
When used, MediaKiller will not execute transcoding tasks but instead compile the tasks into a script file.
This allows you to run batch tasks on a computer that does not have MediaKiller installed.
