# Change logs of cx-studio

### v0.10.0

- **子包重组（10→8）**：`number/`、`collectiontools/` 合并入 `core/`；`iotools/` → `process/`；`tui/` → `clikit/`（扁平化，移除 `tools/` 子层级）。旧路径（`cx_studio.tui`/`.number`/`.collectiontools`/`.iotools`）已移除
- **死代码清理**：删除 `cx_datapackage.py`、`async_canceller.py`、`job_counter.py`、`cx_filesize_counter.py`
- **命名统一**：25 个模块文件去除 `cx_` 前缀。`core/cx_time.py` 系列（`cx_time`/`cx_timebase`/`cx_timerange`）因与 stdlib `time` 冲突保留
- **拼写修正**：`openner.py` → `opener.py`
- **新增 `AGENTS.md`**：子包职责、内部依赖规则、文件命名约定、导出约定、新子包检查清单

### v0.9.2

- 新增 `cx_studio.text.shell_escape` 模块：提供 `escape_arg()` 和 `join_args()` 两个跨平台 Shell 转义函数，用于安全构造命令行参数

### v0.9.0

- **FileSystem 架构重构**：
  - `FileList` 重写为独立模块（`cx_file_list.py`），新增 `clear()` 方法
  - `FileSizer` 提取为独立模块（`cx_file_sizer.py`），`default_sizer` 改为私有
  - `FileInfoCache` 全量重写（435 行 → 更简洁的结构）
  - `CmdFinder` 路径扩展重构（`path_expander/cx_cmdfinder.py`）
  - `FileSizeCounter` 标记为弃用，建议使用 `cx_file_sizer` + `MediaDB`
  - `get_parents()` 修复 off-by-one 错误（`cx_pathutils.py`）
  - `PathExpander` 结构调整
- **PEP 396 规范落地**：所有包新增 `__version__`，`appenv.py` 从 `__init__.py` 导入版本号
- **版本统一**：所有包统一为 0.9.0 同步发布

### v0.8.0.3

- **事件命名规范落地**：为 `DoubleTrigger` 定义事件常量（`TRIGGERED`/`FIRST_TRIGGERED`/`SECOND_TRIGGERED`），内部 `emit()` 全部切换为常量
- **事件重命名**：`FFMPEG_EVENT_VERBOSE` → `FFMPEG_EVENT_VERBOSE_UPDATED`（符合 `-ED` 命名规范），值同步更新为 `"verbose_updated"`
- **旧同步 FFmpeg 迁移**：`cx_ffmpeg.py` 全部 8 处 `emit()` 字面量替换为 `FFMPEG_EVENT_*` 常量
- 全局 `AGENTS.md` 补充 asyncio 事件命名规范章节（`-ED` 形式、常量定义、不在 `__init__.py` 包级导出）

### v0.8.0.2

- 修复 detect_locale() 环境变量检测顺序与 GNU gettext 标准不一致的问题：补充 LANGUAGE、LC_MESSAGES 检测，正确顺序为 LANGUAGE → LC_ALL → LC_MESSAGES → LANG
- LANGUAGE 支持 ":" 分隔的列表，取第一项

### v0.8.0.1

- hotfix: wheel 构建缺少 packages 配置，导致所有 Python 模块未打包进 wheel，运行时 ModuleNotFoundError

### v0.8.0

- 修复了filesystem.encoding_detector在文件较小时输出none的问题。但低置信度下仍然可能输出none。

### v0.7.5

- 新增 CxFileInfoCache 文件信息缓存类
- 修复 FFmpegAsync 中 finally 块内的 return 语句问题
- 全量补充类型注解，清理死代码
- 配置 pyright 类型检查并修复类型安全问题
- 扩展 Python 版本支持范围至 <3.15

### v0.7.0

- 拆分了utils，进行了大量模块层级改动
- 去除了 dydantic 的依赖，重新使用轻量的 dataclass。

### v0.6.3

- 为 SystemUtils 增加了迭代检查文件权限的方法。

### v0.6.1

- 增加了 SystemUtils.flush_dns_cache 方法。

### v0.6.0

- 在 cx_studio.utils 中增加了一个 SystemUtils 模块，提供一些判断操作系统和运行环境的方法。
- 为 path_expander 中添加了一个 SuffixFinder 类，用于快速根据扩展名搜索文件。
- 修改了 FunctionalUtils.flatten_list 方法的实现。

### v0.5.2

- 修复了 FFmpeg 命令行参数预处理的问题。

### v0.5.1.5

- 增加了 FFmpegArgumentsPreProcessor 类，用于预处理 FFmpeg 命令行参数。

### v0.2.1.9

- 为 PathUtils 增加了一个 ensure_parents 方法，用于自动创建文件夹。

### v0.2.1.8

- hotfix: pathexpander 的 macos 兼容性问题

### v0.2.1.7

- 应用 pydantic

### v0.2.1.6

- 删除了没用的文件
- 重新整理的代码格式

### v0.2.1.5

- FFmpeg 同步版本已经可以使用了

### v0.2.1.4

- PathUtils.quote now supports `escape` mode.
- Rewrite ffmpeg(thread safe version).

### v0.2.1.3

- rewrite DataPackage with proper annotations.
- `DataPackage` now supports index of list as key.
