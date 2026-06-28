# HostsKeeper User Guide

> *I'll guard your hosts!*

## Introduction

HostsKeeper is an **intelligent hosts file management tool** that lets you manage system hosts files like you manage code versions. With simple configuration files, you can:

- Pull hosts content directly from network URLs (e.g., hosts repositories on GitHub)
- Reference local files as hosts sources
- Write hosts entries directly in configuration files
- Manage priority across multiple configuration files
- Automatically back up original hosts files
- Preview effects in pretend mode (without actually modifying files)

> Make your hosts file management elegant and powerful!

## Quick Start

### Get Help

```bash
# Ensure running with administrator privileges (Windows)
# Linux/macOS usually does not require it

# View help
hostskeeper help

# Full tutorial
hostskeeper --tutorial
```

### Global Parameters

| Parameter    | Short  | Description                    |
|--------------|--------|--------------------------------|
| `--help`     | `-h`   | Display help information       |
| `--tutorial` | -      | Show detailed tutorial (recommended for beginners) |
| `--debug`    | `-d`   | Enable debug mode, output detailed info |
| `--pretend`  | `-p`   | Pretend mode: preview without actual modification |

## Command Details

### list - List All Configurations

List all discovered configuration files. Use `--search` `-s` parameter for fuzzy search.

```bash
# List all configurations
hostskeeper list

# Search for configurations containing "github"
hostskeeper list -s "*github*"

# Search for configurations containing a specific keyword
hostskeeper list -s "game"
```

**Output example:**

```
+--------+--------------+------------------------+---------+
| ID     | Name         | Description            | Enabled |
+--------+--------------+------------------------+---------+
| google | Google       | Google services access | YES     |
| github | GitHub       | GitHub access acceleration | YES     |
| game   | Game Accel   | Gaming platform hosts  | NO      |
+--------+--------------+------------------------+---------+

Found 3 configuration files.
Try using the show or edit command to view or edit configurations.
```

### show - Display Configuration Details

View the detailed content of a specified configuration file.

```bash
hostskeeper show google
```

**Output example:**

```
+----------------------------------------------------------+
| google                                                    |
+----------------------------------------------------------+
|  name:           Google                                    |
|  description:    Google services access                   |
|  priority:       100                                       |
|  enabled:        true                                      |
|  path:           /Users/xxx/.config/hostskeeper/google.toml|
|                                                                |
|  url_content 0:                                            |
|    url:         https://xxx/hosts                           |
|    description: Fetch Google hosts from network            |
|    encoding:    utf-8                                      |
+----------------------------------------------------------+
```

### new - Create a New Configuration

Create a new hosts configuration file.

```bash
# Create a configuration named my-hosts
hostskeeper new my-hosts

# Opens with the system editor automatically after creation
```

### edit - Edit Configuration

Open the configuration file with the system editor for editing.

```bash
hostskeeper edit google
```

**Tip:** The editor is determined by the `EDITOR` environment variable. If not set, it will try the system default editor.

### update - Update Hosts File

**This is the core command!** Updates the system hosts file based on all enabled configurations.

```bash
# Standard update (requires administrator privileges)
hostskeeper update

# Pretend mode: preview without modification
hostskeeper update -p

# Debug mode: display detailed information
hostskeeper update -d
```

The update command also provides a `--target` `-t` parameter for specifying the hosts file path. The default is the system hosts file.

The update command also provides a `--skip-flush` parameter to skip DNS cache flushing after updating hosts,
and only shows the corresponding manual flush command for each platform:

```bash
# Normal update (auto flush DNS cache)
hostskeeper update

# Skip auto flush, only show manual command hint
hostskeeper update --skip-flush
```

> **Note:** Flushing the DNS cache on Windows requires administrator privileges. The program will automatically attempt an elevated flush after updating hosts.
> macOS requires sudo authorization. Linux does not automatically perform the flush but still shows the hint.

**The update command will automatically detect whether administrator privileges are needed, but currently only supports sudo.**

## Configuration File Format

Configuration files use **TOML** format, stored in the configuration directory (typically `~/.config/hostskeeper/`).

### Complete Example

```toml
[hosts_profile]
profile_id = 'google-hosts'
profile_name = 'Google Services'
description = 'Google family services access acceleration'
enabled = true
priority = 100

# ========== Content source configuration ==========

# Method 1: Fetch from URL
[[url_content]]
url = 'https://raw.githubusercontent.com/racaljk/hosts/master/hosts'
description = 'GitHub hosts mirror'
encoding = 'utf-8'

# Method 2: Load from local file
[[local_content]]
file = './my-custom-hosts.txt'
description = 'Custom hosts entries'
encoding = 'utf-8'

# Method 3: Write directly
[[direct_content]]
ip = '127.0.0.1'
domains = ['localhost', 'dev.local']
comment = 'Local development environment'
```

### Field Description

#### [hosts_profile] - Metadata Section

| Field            | Required | Description                    |
|------------------|----------|--------------------------------|
| `profile_id`     | Yes      | Unique identifier, recommended to use English + hyphens |
| `profile_name`   | Yes      | Display name                   |
| `description`    | No       | Detailed description           |
| `enabled`        | No       | Whether enabled, defaults to `true` |
| `priority`       | No       | Priority, higher number = higher ranking, defaults to `0` |

#### Content Source Configuration

**URL content source** (`url_content`):

```toml
[[url_content]]
url = 'https://example.com/hosts'  # Required: URL address
description = 'Optional description' # Optional: description
encoding = 'utf-8'                   # Optional: encoding, defaults to utf-8
```

**Local content source** (`local_content`):

```toml
[[local_content]]
file = '/path/to/hosts.txt'        # Required: file path (supports absolute/relative)
description = 'Optional description' # Optional: description
encoding = 'utf-8'                   # Optional: encoding, defaults to utf-8
```

**Direct content source** (`direct_content`):

```toml
[[direct_content]]
ip = '127.0.0.1'                    # Required: IP address
domains = ['www.example.com']       # Required: domain list
comment = 'Optional comment'        # Optional: comment description
```

> These content sources are all lists, so they can be freely combined within a single configuration file.

## Practical Examples

### Scenario 1: Internet Access hosts Management

Create a GitHub acceleration configuration:

```bash
hostskeeper new github-accelerator
```

Edit the configuration file:

```toml
[hosts_profile]
profile_id = 'github-accelerator'
profile_name = 'GitHub Accelerator'
description = 'GitHub access acceleration configuration'
enabled = true
priority = 100

[[url_content]]
url = 'https://raw.githubusercontent.com/hollowman/uan/master/hosts'
description = 'GitHub acceleration hosts'
encoding = 'utf-8'
```

Update hosts:

```bash
hostskeeper update -p  # Preview first
hostskeeper update      # Execute after confirmation
```

### Scenario 2: Multi-Environment Development Configuration

```toml
[hosts_profile]
profile_id = 'dev-env'
profile_name = 'Development Environment'
description = 'Local development environment configuration'
enabled = true
priority = 200

# Write development domains directly
[[direct_content]]
ip = '127.0.0.1'
domains = ['dev.example.com', 'staging.example.com']
comment = 'Development environment'

[[direct_content]]
ip = '192.168.1.100'
domains = ['internal-api.local']
comment = 'Internal API service'
```

### Scenario 3: Mixed Content Sources

```toml
[hosts_profile]
profile_id = 'mixed-sources'
profile_name = 'Mixed Configuration'
description = 'Combine hosts from multiple sources'
enabled = true
priority = 50

# Network source
[[url_content]]
url = 'https://example.com/hosts/common'
description = 'Common hosts'

# Local source
[[local_content]]
file = './company-hosts.txt'
description = 'Company internal domains'

# Write directly
[[direct_content]]
ip = '10.0.0.1'
domains = ['corp.local', 'svn.corp.local']
comment = 'Company internal services'
```

## Security Mechanisms

### Automatic Backup

Each time the hosts file is updated, the original file is automatically backed up:

- **Backup directory**: `~/.config/hostskeeper/backups/`
- **Backup filename**: `YYYYMMDD_HHMMSS_xxxxx.bak`
- **Backup count**: Managed by the user (no automatic cleanup at present)

### Permission Check

```python
# Handling for non-admin
if not is_admin():
    appenv.say("[warning] Not running with admin privileges, will force pretend mode")
    pretending = True
```

### Pretend Mode

Use the `-p` parameter for a safe preview:

```bash
hostskeeper update -p
```

This will:

1. [OK] Generate the complete hosts content
2. [OK] Print to terminal for your review
3. [NO] **Will not** modify any files
4. [NO] **Will not** create backups

## Priority Mechanism

Hosts entries from multiple configuration files are merged according to the following rules:

1. **Higher priority configurations are output first** (larger priority value = higher rank)
2. **Same domain: later occurrence overwrites earlier**
3. **Configuration sections are clearly marked** (for easy identification and manual maintenance)

```
Original hosts free area
------------------------------
[google START]                 # High priority configuration
Google-related entries...
[google END]
------------------------------
[github START]                 # Low priority configuration
GitHub-related entries...
[github END]
------------------------------
Original hosts free area
```

## Troubleshooting

### Issue 1: Update Failed, Insufficient Permissions

**Symptom**:

```
[cx.error] Failed to open file: Permission denied
```

**Solutions**:

- **Windows**: Right-click -> "Run as administrator"
- **Linux/macOS**: Usually not required, add `sudo` if permission issues arise

### Issue 2: Configuration File Not Found

**Symptom**:

```
[cx.error] Configuration file with ID xxx not found
```

**Investigation steps**:

```bash
# 1. List all configurations
hostskeeper list

# 2. Check configuration directory
# Windows: %APPDATA%/hostskeeper/
# Linux/macOS: ~/.config/hostskeeper/

# 3. Ensure configuration files end with .toml
```

### Issue 3: URL Content Source Download Failed

**Symptom**:

```
url_content parse failed
```

**Possible causes**:

- Network connection issues
- URL is no longer valid
- Encoding issues

**Solutions**:

```bash
# 1. Test the URL with curl first
curl -I https://your-url.com/hosts

# 2. Check encoding setting
# Ensure it matches the actual encoding
encoding = 'utf-8'  # or gbk, gb2312, etc.
```

### Issue 4: Hosts Parse Error

**Symptom**:

```
Unparseable entries found in configuration file
```

**Check format**:

```toml
# Correct format
ip = '127.0.0.1'
domains = ['www.example.com']

# Domains should be in array form
domains = 'www.example.com'  # Wrong
domains = ['www.example.com'] # Correct
```

## Debugging Tips

### Enable Debug Mode

```bash
hostskeeper update -d
```

Debug mode will display:

- List of discovered configuration files
- Detailed information for each configuration file
- Content processing progress
- The final generated hosts content

### View Help Information

```bash
# Short help
hostskeeper help

# Full tutorial (recommended)
hostskeeper --tutorial
```

## Best Practices

1. **Take small steps**: After creating a new configuration, preview with `-p` first, then update once confirmed correct
2. **Version control**: Include configuration files in Git management (be mindful of sensitive information)
3. **Regular backups**: Keep backups of important hosts versions
4. **Reasonable priority**: Set higher priority for frequently used configurations to avoid being overwritten
5. **Clear comments**: Add descriptions to each configuration and entry for easier maintenance

---

**Happy hosting!** ^_^

> *Have questions? File an Issue on GitHub!*  
> *Project URL: https://github.com/LambdaXIII/cx-studio-tk*
