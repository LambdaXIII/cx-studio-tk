# cxnote User Guide

> *A quick sticky note in your terminal — fast to jot, light to scan.*

## Intro

cxnote is a minimal terminal note / to-do tool. Every entry lives in one JSON file, organized by **domain**; daily use is just one verb plus one argument:

```bash
cxnote add "buy milk"     # jot one entry
cxnote                    # view the current domain
cxnote finish milk        # done — cross it off
```

## Domains and the Working Domain

A **domain** is the path an entry belongs to, like `/work/project-a`. Your current directory decides the **working domain**:

- Running `cxnote add "fix bug"` under `~/projects/app` records the entry into the domain for that project;
- Without `-p` / `-g`, every command works inside the current working domain;
- The list shows only the working domain's entries by default; sub-domains appear as collapsed header lines (expand with `--full`).

| Flag | Effect |
|---|---|
| `-p` / `--path` | Switch the working domain: starting with `/` means an absolute domain, otherwise relative to the current one; **applies to all verbs** |
| `-g` / `--global` | Work directly in the root domain |

```bash
cxnote -p /chores add "pay the utility bill"   # record into an absolute domain
cxnote -p /app/backend list                     # browse another domain
cxnote -g list --full                           # root-domain overview
```

## Command Overview

| Command | Argument | Description |
|---|---|---|
| `add` | text | Record one entry into the working domain; `\n` in the text becomes a line break; **an exactly identical entry in the same domain is never duplicated** (the existing entry is reported back) |
| `list` | — (default verb) | Show entries grouped by domain; `--full` expands sub-domains |
| `finish` | ID or text fragment | Mark as done and stamp the completion time |
| `pend` | ID or text fragment | Move to in-progress |
| `reset` | ID or text fragment | Reset to todo and clear the completion time |
| `erase` | ID or text fragment | Delete one entry |
| `clear` | — | Empty the working domain's direct entries (sub-domains excluded), with one interactive confirmation |

```bash
cxnote add "weekend\n- hike\n- groceries"   # a multi-line entry
cxnote pend hike                            # move to in-progress
cxnote finish a1b2                          # finish by ID
cxnote erase a1b2                           # delete one entry
cxnote clear                                # empty the current domain (asks first)
```

## Status Transitions

Each note has one of three states: `todo` → `pending` → `done`.

- Only `done` carries a completion time; `reset` / `pend` clear it;
- List markers: `[ ]` todo, `[~]` in-progress, `[x]` done.

## Three Ways to Delete

1. **`erase <id|text>`** — remove one entry;
2. **`clear`** — empty the working domain's direct entries (**sub-domains excluded**); the human-readable mode asks once, `--json` skips the prompt;
3. **Automatic cleanup** — there is no manual clean command: every write (add / finish / pend / reset / erase / clear) also removes **completed entries past the retention period** set in the config (see below).

## Target Resolution

The argument of `finish` / `pend` / `reset` / `erase` may be:

- **ID**: every entry has a 4-character ID (the badge at the end of its list row) — **exact match, library-wide**;
- **text fragment**: substring matching within the **visible domains** (current + sub-domains) only, and it **must hit exactly one** entry — multiple hits list the candidates and ask you to use the ID instead.

## JSON Output

With `--json`, stdout carries pure JSON only (title, hints and the confirmation prompt are all skipped) — built for scripts:

```bash
cxnote list --json                 # array of current-domain entries
cxnote list --json --full          # current domain + all sub-domains
cxnote add "ticket" --json         # the new entry object (existing one on duplicates — idempotent)
cxnote finish a1b2 --json          # the updated entry object
cxnote clear --json                # array of the removed entries (no prompt)
```

Entry objects always carry the same six keys: `id` / `domain` / `content` / `status` / `created_at` / `completed_at` (`completed_at` is `null` until done).

## Configuration File

On first run, `config.toml` is created automatically in the config directory:

```toml
retention_days = 30
```

- `retention_days`: how many days completed entries are kept; overdue ones are removed during write operations;
- `0` or negative disables automatic cleanup;
- To adjust the retention period, edit the file directly (there is no config command).

## Getting Help

```bash
cxnote -h            # grouped help
cxnote --tutorial    # this guide
```

> *Project: https://github.com/LambdaXIII/cx-studio-tk*
