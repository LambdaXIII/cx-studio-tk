# cxnote User Guide

> *A quick sticky note in your terminal — fast to jot, light to scan.*

## Intro

cxnote is a minimal terminal note / to-do tool. Every entry lives in one JSON file, organized by **domain**; daily use is just one verb plus one or more arguments:

```bash
cxnote add "buy milk" "pay utility bill"    # jot multiple entries
cxnote                                       # view the current domain
cxnote finish milk                           # done — cross it off
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
| `add` | text (multiple allowed) | Record one or more entries into the working domain; each argument becomes one entry; `\n` in the text becomes a line break; **an exactly identical entry in the same domain is never duplicated** (the existing entry is reported back) |
| `list` | — (default verb) | Show entries grouped by domain; `--full` expands sub-domains |
| `finish` | ID or text fragment (multiple allowed) | Mark as done and stamp the completion time |
| `pend` | ID or text fragment (multiple allowed) | Move to in-progress |
| `reset` | ID or text fragment (multiple allowed) | Reset to todo and clear the completion time |
| `drop` | ID or text fragment (multiple allowed) | Mark as cancelled; the entry remains in the store |
| `erase` | ID or text fragment (multiple allowed) | Delete one or more entries |
| `clear` | — | Empty the working domain's direct entries (sub-domains excluded), with one interactive confirmation |

```bash
cxnote add "weekend\n- hike\n- groceries" "buy groceries"    # batch: record two entries
cxnote pend hike                                               # move to in-progress
cxnote finish a1b2 b3c4                                        # batch: finish two entries
cxnote drop buy groceries                                      # cancel one entry
cxnote erase a1b2 b3c4                                        # batch: delete two entries
cxnote clear                                                   # empty the current domain (asks first)
```

**Batch argument rules**: entry-level verbs (`add`, `finish`, `pend`, `reset`, `drop`, `erase`) accept multiple arguments, each becoming one target. If any argument fails to resolve, the entire command is aborted with no partial effect, and the error lists every problematic argument. An explicit argument that is empty after `strip` causes an abort (e.g. a misquoted empty string), never a silent skip.

**Post-operation echo**: after every verb except `list` succeeds in human-readable mode, the current working domain's **direct entry list** is printed below the confirmation line — all statuses, no sub-domains (not even their header lines). Use `list` to see sub-domains; an empty domain echoes "no entries".

## Status Transitions

Each note has one of four states: `todo` → `pending` → `done` / `dropped`.

- `done` (completed) and `dropped` (cancelled) are both **terminal states**;
- Terminal states carry a completion time (`completed_at`) — stamped on entry, cleared on exit (`reset` / `pend`);
- A cancelled entry may be directly `finish`ed or `reset` without any guard;
- List markers: `[ ]` todo, `[~]` in-progress, `[x]` done, `[-]` dropped (dim + strike).

## Three Ways to Delete

1. **`erase <id|text>`** — remove one or more entries;
2. **`clear`** — empty the working domain's direct entries (**sub-domains excluded**); the human-readable mode asks once, `--json` skips the prompt;
3. **Automatic cleanup** — every write operation (add / finish / pend / reset / erase / clear / drop) also removes **completed and cancelled entries past the retention period** (terminal-state entries). The retention period is set in the config (see below).

## Target Resolution

The argument of `finish` / `pend` / `reset` / `drop` / `erase` may be:

- **ID**: every entry has a 4-character ID (the badge at the end of its list row) — **exact match, library-wide**;
- **text fragment**: substring matching within the **visible domains** (current + sub-domains) only, and it **must hit exactly one** entry — multiple hits list the candidates and ask you to use the ID instead.

## JSON Output

With `--json`, stdout carries pure JSON only (title, hints, the confirmation prompt and the post-operation echo are all skipped) — built for scripts:

```bash
cxnote list --json                          # array of current-domain entries
cxnote list --json --full                   # current domain + all sub-domains
cxnote add "ticket" --json                  # single-element array (one entry object)
cxnote add "milk" "eggs" --json             # array of two new entry objects
cxnote finish a1b2 --json                   # single-element array (the updated entry)
cxnote erase a1b2 b3c4 --json               # array of two deleted entry objects
cxnote add "milk" --json                    # duplicate: returns array with the existing entry object
cxnote clear --json                         # array of removed entries (no prompt)
```

Entry objects always carry the same six keys: `id` / `domain` / `content` / `status` / `created_at` / `completed_at` (`completed_at` is `null` until done). Batch `--json` output is an array of entry objects (single argument still produces a single-element array), in argument order; duplicate hits in `add` output existing entry objects. On failure, stdout is empty and errors go to stderr.

## Configuration File

On first run, `config.toml` is created automatically in the config directory:

```toml
retention_days = 30
```

- `retention_days`: how many days terminal-state entries (completed and cancelled) are kept; overdue entries are removed during write operations;
- `0` or negative disables automatic cleanup;
- To adjust the retention period, edit the file directly (there is no config command).

## Getting Help

```bash
cxnote -h            # grouped help
cxnote --tutorial    # this guide
```

> *Project: https://github.com/LambdaXIII/cx-studio-tk*
