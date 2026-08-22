# Contributing to cx-studio-tk

Thanks for your interest in contributing! This document covers development setup, code conventions, and the internationalization (i18n) workflow.

## Development Setup

```shell
git clone git@github.com:LambdaXIII/cx-studio-tk.git
cd cx-studio-tk
uv sync
```

The repository is a `uv` workspace. Run all commands from the workspace root unless stated otherwise.

For development dependencies:

```shell
uv sync --group dev
```

Requires Python >= 3.12, < 3.15.

## Code Conventions

- Format with `black` before committing — it's the project's only formatter:
  ```shell
  uv run black .
  ```
- Add docstrings to new public functions and classes.
- Follow the conventions described in `AGENTS.md` (naming, import rules, data model choices, display protocol, asyncio event naming, etc.).
- Target platforms are Windows / macOS / Linux. Use `pathlib.Path` for path operations and always specify `encoding="utf-8"` for file I/O.

## Contributing Workflow

- Work on a feature branch branched from `dev` (`feat/<desc>` / `fix/<desc>` / `chore/<desc>`), then merge back to `dev`.
- Never push directly to `main` — it only receives `--no-ff` merges from `dev`.
- Commit format: `type(scope): description` (type: feat/fix/docs/chore/refactor).
- Modify `pyproject.toml` (add dependency) and version numbers (`__version__` and `pyproject.toml`) only with the owner's confirmation.
- Add a `[最新修改]` section to the top of `CHANGELOG.md` after any content change; it becomes a version section on the next release.
- Do not delete `.env` or non-temporary config files (`pyproject.toml`, `.github/`, CI config).

## Internationalization (i18n)

The project uses **gettext + Babel**. Each distributable package maintains its own translation files under its source directory:

| Package | Translation File Location | Domain |
|---|---|---|
| cx-studio | `cx_studio/i18n/locales/` | `cx-studio` |
| cxalio-studio-tools (framework) | `cx_tools/i18n/locales/` | `cx-tools` |
| cxalio-studio-tools / media_scout | `media_scout/i18n/locales/` | `media-scout` |
| cxalio-studio-tools / media_killer | `media_killer/i18n/locales/` | `media-killer` |
| cxalio-studio-tools / jpegger | `jpegger/i18n/locales/` | `jpegger` |
| cxalio-studio-tools / hosts_keeper | `hosts_keeper/i18n/locales/` | `hosts-keeper` |

> **Source Language Policy**: The standard language of this project is Simplified Chinese (zh_CN). `_()` calls in the code use Chinese as the msgid, with translations (including English) supplied via `.po` `msgstr`. Since the source language is Simplified Chinese, do **not** create a `zh_CN` `.po`/`.mo` file — gettext falls back to the msgid when no `.mo` is found, and an empty `msgstr` would override it with an empty string.

### Quick Start for Translators

1. Locate the `.po` file for the package you want to translate, e.g. `cx_tools/i18n/locales/en_US/LC_MESSAGES/cx-tools.po`.
2. Open it with **Poedit** (recommended) or any text editor, fill `msgstr ""` with your target language.
3. Save and submit a Pull Request.

You can verify the `.po` compiles correctly to `.mo` using the full command (e.g. `uv run pybabel compile --domain cx-tools --directory cx_tools/i18n/locales`, executed in the corresponding package directory). Compiled `.mo` files are committed to git — users do not run compilation at install time.

### Workflow for Developers

Wrap user-facing strings with `_()` in code:

```python
from cx_studio.i18n import _   # inside cx-studio package
from cx_tools.i18n import _    # inside cxalio-studio-tools package

appenv.say(_("程序正常退出。"))

# Strings with variables — variables go outside _()
appenv.say(_("已处理 {count} 个文件。").format(count=n))

# Plural forms
from cx_tools.i18n import _ng
appenv.say(_ng("找到 {n} 个结果", "找到 {n} 个结果", n).format(n=n))
```

**Import rules**: Tool modules must import from their own tool's `i18n` module — a module in `media_killer` imports from `media_killer.i18n`, never cross-import `cx_tools.i18n`. The `cx_tools` framework's own modules still import from `cx_tools.i18n`.

Rules:
- Only wrap **user-facing fixed text** — not variables, file paths, command-line argument names, FFmpeg output, error traces, or debug-only logs.
- Rich markup tags (`[cx.error]`, `[green]`) stay outside, never inside `_()`.
- After adding new strings, run the extraction command to update the `.po` template.

### Extract-Translate-Compile Cycle

Run in the corresponding package directory.

For cx-studio (`packages/cx-studio/`):

```shell
uv run pybabel extract --mapping babel.cfg --output-file cx_studio/i18n/locales/cx-studio.pot --project cx-studio --copyright-holder 'Cxalio' .
uv run pybabel update --domain cx-studio --input-file cx_studio/i18n/locales/cx-studio.pot --output-dir cx_studio/i18n/locales
uv run pybabel compile --domain cx-studio --directory cx_studio/i18n/locales
```

For cxalio-studio-tools — extract each tool separately (`packages/cxalio-studio-tools/`):

```shell
uv run pybabel extract -k _ --output-file cx_tools/i18n/locales/cx-tools.pot cx_tools/
uv run pybabel extract -k _ --output-file media_scout/i18n/locales/media-scout.pot media_scout/
uv run pybabel extract -k _ --output-file media_killer/i18n/locales/media-killer.pot media_killer/
uv run pybabel extract -k _ --output-file ffpretty/i18n/locales/ffpretty.pot ffpretty/
uv run pybabel extract -k _ --output-file jpegger/i18n/locales/jpegger.pot jpegger/
uv run pybabel extract -k _ --output-file hosts_keeper/i18n/locales/hosts-keeper.pot hosts_keeper/
```

Then `update` and `compile` for each tool:

```shell
uv run pybabel update -i cx_tools/i18n/locales/cx-tools.pot -d cx_tools/i18n/locales -l en_US -D cx-tools
uv run pybabel compile -d cx_tools/i18n/locales -l en_US -D cx-tools
```

(Repeat for media_scout, media_killer, ffpretty, jpegger, hosts_keeper.)

### Locale Detection

`gettext` selects the locale in the order `LANGUAGE` → `LC_ALL` → `LC_MESSAGES` → `LANG`.

Note: terminals often set `LC_ALL=C.UTF-8`, which overrides `LANG` and causes locale detection to fall back to `C`, so translation `.mo` files are not loaded (`_()` then returns the Chinese msgid). This is standard POSIX behavior, not a bug.

To test another language's translations, clear `LC_ALL` and set `LANG`:

```bash
LC_ALL= LANG=en_US.UTF-8 hostskeeper --help
```

### Help Text (help.md)

Help text uses filename suffixes to distinguish languages:

```
help.md            # Chinese (source language)
help.en_US.md      # English
```

Help text contains no `_()` calls. Translators copy `help.md` to `help.<locale>.md` and translate section by section.
