# Media Scout

Media Scout can parse common video editing project files
and extract media file paths from them.

Supported file types include:

- Classical XML project files (Final Cut Pro 7 XML) `.xml`
- FCPXML project files (Final Cut Pro X|11 XML) `.fcpxml` or `.fcpxmld`
- Editing Decision Lists `.edl`
- Davinci Resolve metadata tables `.csv`
- Plain text file lists `.txt`
  Plain text files can also be `.sh` script files containing paths. Media Scout will use regular expressions to extract paths from the text.

## Usage

Use it directly:

```shell
mediascout "project1.xml" "project2.fcpxml" "project3.edl" "project4.csv" "project5.txt" "project6.sh" ...
```

By default, mediascout will parse supported files one by one
and output the parsed results line by line to `stdout`.

You can redirect the output directly:

```shell
mediascout "sequence.xml" > "output.txt"
```

mediascout has some default characteristics:

- File paths from the project file are output in their original order
- If multiple project files are specified, they are parsed one by one in input order
- Parsed files are output as-is in string form
- Each line outputs one path
- Duplicate paths will not be output during a single execution, even if they come from different files

Be aware of these characteristics to ensure the tool's output meets your expectations.
Additionally, these characteristics can be customized through options.

## Advanced Options

Media Scout provides various options to customize its behavior
to suit your needs.

### `-i|--include`

For formats like `EDL`,
the format itself does not store the full path of source files —
only filenames can be parsed from it.

Use the `--include` option to specify a directory; it can also be used multiple times to specify multiple directories.
When Media Scout encounters a non-absolute path, it will automatically search these directories for the file.
If found, the full path is output; otherwise, the original relative path is kept.

### `-e|--existed-only`

The `--existed-only` option filters out paths that do not exist.

If a path is relative and no `--include` option is specified, the lookup will start from the current working directory.

### `--allow-duplicated`

Although I don't really understand what use this is, this option disables the automatic deduplication feature.

### `-q|--auto-quote`

When this option is specified, paths containing spaces will be automatically quoted.
