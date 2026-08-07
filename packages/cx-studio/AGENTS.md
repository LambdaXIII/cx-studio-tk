# cx-studio 开发指南

`cx-studio` 是 monorepo 中所有包的基础设施库，提供值对象、系统抽象、文件操作、FFmpeg 封装等通用能力。不放业务逻辑或特定工具的实现。

本文件与仓库根 `AGENTS.md` 叠加生效——根文件为全局基线，本文件补充 cx-studio 包独有的约定。

---

## 子包目录与职责

重组后共 8 个子包，按"领域/功能"维度划分：

|子包|职责|核心符号|
|---|---|---|
|`core/`|基础值对象与工具函数|`CxTime`, `Timebase`, `TimeRange`, `FileSize`, `NumberRange`, `quick_clamp`, `quick_remap`, `flatten_list`, `iter_with_separator`, `split_to_two`|
|`text/`|文本处理|字符串工具、Shell 转义、`TagReplacer`、`PathInfoProvider`|
|`filesystem/`|文件系统操作|`PathUtils`, `CmdFinder`, `PathExpander`, `FileList`, `FileSizer`, `FileInfoCache`, `detect_file_encoding`|
|`system/`|系统抽象|`SystemType`, `CrossRunner`, `system_open`, `is_user_admin`|
|`clikit/`|CLI 工具基础设施|`DoubleTrigger`, `FIRST_TRIGGERED`, `SECOND_TRIGGERED`|
|`process/`|子进程与流处理|同步/异步版本的子进程创建、流读写、行解析|
|`ffmpeg/`|FFmpeg 封装|同步/异步执行器、编码信息数据类、错误类型层级、参数预处理器|
|`i18n/`|国际化基础设施|`gettext` 工厂函数、locale 检测、本地化文本加载器|

---

## 内部依赖规则

严格遵守，不可反向：

```
i18n        ← 无内部依赖
core        → i18n
text        → core, i18n
process     → i18n
filesystem  → core, i18n, process
system      → i18n
clikit      → i18n
ffmpeg      → core, filesystem, process, i18n
```

---

## 文件命名

- 模块文件名不含 `cx_` 前缀（包名 `cx_studio` 已提供命名空间）
- 例外：去前缀后与 Python 标准库模块重名时，保留 `cx_` 前缀。同一"系列"的模块统一处理
  - 当前仅 `core/cx_time.py` 与 stdlib `time` 冲突，故 `cx_time.py`、`cx_timebase.py`、`cx_timerange.py` 保留前缀
- 新增模块直接使用短命名

---

## 导出约定

- 每个子包通过 `__init__.py` 使用 `from .module import *` 汇聚所有公开符号
- 对外暴露的类/函数使用明确的公开名（无下划线前缀），内部实现使用 `_` 前缀
- 必要时在 `__init__.py` 中定义 `__all__` 列表

---

## 禁止放入 cx-studio 的内容

- 特定 CLI 工具的业务逻辑 → 属于 `cxalio-studio-tools`
- Rich UI 组件 → 属于 `cx-wealthy`
- 应用生命周期管理 → 属于 `cx_tools.app`
- 只被单一工具使用的专用代码 → 放该工具内部

## 时间域与开放库原则

**时间域（CxTime/Timebase/TimeRange/timecode）是多年积累的核心资产**：直接兼容工业标准（时间码）、毫秒级精度为刻意设计、将来有广泛用途（时间线解析等）。禁止以"零引用"为由删除。

**开放库原则**：cx-studio 是开放功能库，仓库内零引用 ≠ 死代码（外部消费者不可见）。删除公开 API 需作者确认不可用/未完成/未文档化。

---

## 添加新子包的检查清单

1. 是否至少包含 3+ 个有意义且相互关联的模块？若不足 3 个，考虑放入现有子包
2. 是否属于"通用基础设施"？若仅被一个工具使用，放该工具内部
3. 是否与现有子包存在明确的边界？新子包的定位不与已有子包重叠
