# HostsKeeper 使用指南

> *你的 hosts 由我来守护！*

## 项目简介

HostsKeeper 是一个**智能 hosts 文件管理工具**，它能让你像管理代码版本一样管理系统 hosts 文件。通过简单的配置文件，你可以：

- 从网络 URL 直接拉取 hosts 内容（如 GitHub 上的 hosts 仓库）
- 引用本地文件作为 hosts 来源
- 直接在配置文件中编写 hosts 记录
- 多配置文件的优先级管理
- 自动备份原 hosts 文件
- 假装模式预览效果（不实际修改文件）

> 让你的 hosts 文件管理变得优雅而强大！

## 快速上手

### 获取帮助

```bash
# 确保以管理员权限运行（Windows）
# Linux/macOS 通常不需要

# 查看帮助
hostskeeper help

# 完整教程
hostskeeper --tutorial
```

### 全局参数

| 参数           | 简写   | 说明             |
|--------------|------|----------------|
| `--help`     | `-h` | 显示帮助信息         |
| `--tutorial` | -    | 显示详细教程（推荐新手查看） |
| `--debug`    | `-d` | 开启调试模式，输出详细信息  |
| `--pretend`  | `-p` | 假装模式：只预览不实际修改  |

## 命令详解

### list - 列出所有配置文件

列出所有发现的配置文件。使用 `--search` `-s` 参数模糊搜索。

```bash
# 列出所有配置文件
hostskeeper list

# 搜索包含 "github" 的配置
hostskeeper list -s "*github*"

# 搜索包含特定关键词的配置
hostskeeper list -s "游戏"
```

**输出示例：**

```
+--------+--------------+------------------------+---------+
| ID     | Name         | Description            | Enabled |
+--------+--------------+------------------------+---------+
| google | Google       | Google 服务访问        | YES     |
| github | GitHub       | GitHub 访问加速        | YES     |
| game   | 游戏加速     | 游戏平台hosts          | NO      |
+--------+--------------+------------------------+---------+

共找到 3 个配置文件。
可尝试使用 show 或 edit 命令查看或编辑配置文件。
```

### show - 显示配置详情

查看指定配置文件的详细内容。

```bash
hostskeeper show google
```

**输出示例：**

```
+----------------------------------------------------------+
| google                                                    |
+----------------------------------------------------------+
|  name:           Google                                    |
|  description:    Google 服务访问                          |
|  priority:       100                                       |
|  enabled:        true                                      |
|  path:           /Users/xxx/.config/hostskeeper/google.toml|
|                                                                |
|  url_content 0:                                            |
|    url:         https://xxx/hosts                           |
|    description: 从网络获取 Google hosts                     |
|    encoding:    utf-8                                      |
+----------------------------------------------------------+
```

### new - 创建新配置

创建一个新的 hosts 配置文件。

```bash
# 创建名为 my-hosts 的配置
hostskeeper new my-hosts

# 创建后会自动用系统编辑器打开
```

### edit - 编辑配置

用系统编辑器打开配置文件进行编辑。

```bash
hostskeeper edit google
```

**提示：** 编辑器由 `EDITOR` 环境变量决定，如未设置会尝试系统默认编辑器。

### update - 更新 hosts 文件

**这是最核心的命令！** 根据所有启用的配置文件更新系统的 hosts 文件。

```bash
# 标准更新（需要管理员权限）
hostskeeper update

# 假装模式：只预览不修改
hostskeeper update -p

# 调试模式：显示详细信息
hostskeeper update -d
```

另外 update 命令提供一个 `--target` `-t` 参数，用于指定 hosts 文件路径。默认是系统 hosts 文件。

**update 命令将会自动识别是否需要调用管理员权限，但目前只支持 sudo。**

## 配置文件格式

配置文件使用 **TOML** 格式，放在配置目录下（通常为 `~/.config/hostskeeper/`）。

### 完整示例

```toml
[hosts_profile]
profile_id = 'google-hosts'
profile_name = 'Google 服务'
description = 'Google 全家桶访问加速'
enabled = true
priority = 100

# ========== 以下为内容源配置 ==========

# 方式一：从 URL 获取
[[url_content]]
url = 'https://raw.githubusercontent.com/racaljk/hosts/master/hosts'
description = 'GitHub hosts 镜像'
encoding = 'utf-8'

# 方式二：从本地文件加载
[[local_content]]
file = './my-custom-hosts.txt'
description = '自定义 hosts 记录'
encoding = 'utf-8'

# 方式三：直接编写
[[direct_content]]
ip = '127.0.0.1'
domains = ['localhost', 'dev.local']
comment = '本地开发环境'
```

### 字段说明

#### [hosts_profile] - 元数据区域

| 字段             | 必填 | 说明                 |
|----------------|----|--------------------|
| `profile_id`   | OK | 唯一标识符，建议使用英文+连字符   |
| `profile_name` | OK | 显示名称               |
| `description`  | -  | 详细描述               |
| `enabled`      | -  | 是否启用，默认为 `true`    |
| `priority`     | -  | 优先级，数字越大越靠前，默认 `0` |

#### 内容器配置

**URL 内容器** (`url_content`)：

```toml
[[url_content]]
url = 'https://example.com/hosts'  # 必须：URL 地址
description = '可选说明文字'         # 可选：描述
encoding = 'utf-8'                  # 可选：编码，默认 utf-8
```

**本地内容器** (`local_content`)：

```toml
[[local_content]]
file = '/path/to/hosts.txt'        # 必须：文件路径（支持绝对/相对）
description = '可选说明文字'         # 可选：描述
encoding = 'utf-8'                  # 可选：编码，默认 utf-8
```

**直接内容器** (`direct_content`)：

```toml
[[direct_content]]
ip = '127.0.0.1'                    # 必须：IP 地址
domains = ['www.example.com']       # 必须：域名列表
comment = '可选注释'                 # 可选：注释说明
```

> 这些内容器都是列表，所以在一个配置文件中可以自由组合使用。

## 实战示例

### 场景一：科学上网 hosts 管理

创建一个 GitHub 加速配置：

```bash
hostskeeper new github-accelerator
```

编辑配置文件：

```toml
[hosts_profile]
profile_id = 'github-accelerator'
profile_name = 'GitHub 加速'
description = 'GitHub 访问加速配置'
enabled = true
priority = 100

[[url_content]]
url = 'https://raw.githubusercontent.com/hollowman/uan/master/hosts'
description = 'GitHub 加速 hosts'
encoding = 'utf-8'
```

更新 hosts：

```bash
hostskeeper update -p  # 先预览
hostskeeper update      # 确认后执行
```

### 场景二：多环境开发配置

```toml
[hosts_profile]
profile_id = 'dev-env'
profile_name = '开发环境'
description = '本地开发环境配置'
enabled = true
priority = 200

# 直接编写开发域名
[[direct_content]]
ip = '127.0.0.1'
domains = ['dev.example.com', 'staging.example.com']
comment = '开发环境'

[[direct_content]]
ip = '192.168.1.100'
domains = ['internal-api.local']
comment = '内部 API 服务'
```

### 场景三：混合内容源

```toml
[hosts_profile]
profile_id = 'mixed-sources'
profile_name = '混合配置'
description = '组合多种来源的 hosts'
enabled = true
priority = 50

# 网络源
[[url_content]]
url = 'https://example.com/hosts/common'
description = '通用 hosts'

# 本地源
[[local_content]]
file = './company-hosts.txt'
description = '公司内部域名'

# 直接编写
[[direct_content]]
ip = '10.0.0.1'
domains = ['corp.local', 'svn.corp.local']
comment = '公司内部服务'
```

## 安全机制

### 自动备份

每次更新 hosts 文件时，会自动备份原文件：

- **备份目录**：`~/.config/hostskeeper/backups/`
- **备份文件名**：`YYYYMMDD_HHMMSS_xxxxx.bak`
- **备份数量**：用户自行管理（目前不会自动清理）

### 权限检查

```python
# 非管理员运行时的处理
if not is_admin():
    appenv.say("[warning]当前非管理员权限，将强制使用假装模式")
    pretending = True
```

### 假装模式

使用 `-p` 参数可以安全预览：

```bash
hostskeeper update -p
```

这会：

1. [OK] 生成完整的 hosts 内容
2. [OK] 打印到终端供你检查
3. [NO] **不会**修改任何文件
4. [NO] **不会**创建备份

## 优先级机制

多个配置文件的 hosts 记录按以下规则合并：

1. **优先级高的配置先输出**（priority 数值越大越靠前）
2. **相同域名的后出现者覆盖前者**
3. **配置区间有明确标记**（便于识别和手动维护）

```
原有 hosts 自由区域
------------------------------
[google START]                 # 高优先级配置
Google 相关记录...
[google END]
------------------------------
[github START]                 # 低优先级配置
GitHub 相关记录...
[github END]
------------------------------
原有 hosts 自由区域
```

## 故障排查

### 问题 1：更新失败，提示权限不足

**症状**：

```
[cx.error]打开文件失败：权限被拒绝
```

**解决方案**：

- **Windows**：右键 -> "以管理员身份运行"
- **Linux/macOS**：通常不需要，如遇权限问题加 `sudo`

### 问题 2：找不到配置文件

**症状**：

```
[cx.error]未找到 ID 为 xxx 的配置文件
```

**排查步骤**：

```bash
# 1. 列出所有配置
hostskeeper list

# 2. 检查配置目录
# Windows: %APPDATA%/hostskeeper/
# Linux/macOS: ~/.config/hostskeeper/

# 3. 确认配置文件以 .toml 结尾
```

### 问题 3：URL 内容器下载失败

**症状**：

```
url_content 解析失败
```

**可能原因**：

- 网络连接问题
- URL 已失效
- 编码问题

**解决方案**：

```bash
# 1. 先用 curl 测试 URL
curl -I https://your-url.com/hosts

# 2. 检查 encoding 设置
# 确保与实际编码匹配
encoding = 'utf-8'  # 或 gbk, gb2312 等
```

### 问题 4：hosts 解析错误

**症状**：

```
配置文件中存在无法解析的条目
```

**检查格式**：

```toml
# 正确格式
ip = '127.0.0.1'
domains = ['www.example.com']

# 域名应该是数组形式
domains = 'www.example.com'  # 错误
domains = ['www.example.com'] # 正确
```

## 调试技巧

### 开启调试模式

```bash
hostskeeper update -d
```

调试模式会显示：

- 发现的配置文件列表
- 每个配置文件的详细信息
- 内容处理进度
- 最终生成的 hosts 内容

### 查看帮助信息

```bash
# 简短帮助
hostskeeper help

# 完整教程（推荐）
hostskeeper --tutorial
```

## 最佳实践

1. **小步慢跑**：创建新配置后先用 `-p` 预览，确认无误再真正更新
2. **版本控制**：将配置文件纳入 Git 管理（注意敏感信息）
3. **定期备份**：保留重要版本的 hosts 备份
4. **合理优先级**：常用配置设高优先级，避免被覆盖
5. **注释清晰**：给每个配置和记录添加说明，便于维护

---

**祝使用愉快！** ^_^

> *有问题？去 GitHub 提 Issue 吧！*  
> *项目地址：https://github.com/LambdaXIII/cx-studio-tk*
