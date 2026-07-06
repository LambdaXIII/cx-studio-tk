# media_killer 重构范围与旧版参考指南

> 本文档锚定本次重构的**确定内容**（修改范围、可直接沿用的文件）与**可参考内容**（旧版代码的参考层级）。
>
> **最高原则**：以新版设计文档为准，旧版代码仅作参考。本次重构**不是把旧版代码重组成新结构**，而是根据新设计重新编写正确的实现，同时保证功能不缺失、行为不偏差。

---

## 1. 预期修改范围

### 1.1 允许修改的文件范围

本次重构只允许修改以下两类内容：

1. **`packages/cxalio-studio-tools/media_killer/` 包内全部代码**
   - 当前该目录仅包含设计文档，需从零实现整个包。
   - 包含：CLI 入口、AppEnv、Mission 系统、Executor、Scheduler、Preset 系统、SourceExpander、MediaDB/MediaProber、MissionStore、ScriptMaker、主题模块等。

2. **`packages/cx-studio/cx_studio/filesystem/cx_file_info_cache.py` 单文件**
   - 按 [MEDIA_PROBER_AND_CACHE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md) 重新设计 `FileInfoCache`。
   - 该文件保留在 `cx-studio` 中作为通用组件，但本次纳入实现范围。

### 1.2 明确禁止修改的文件

- **旧版 `packages/cxalio-studio-tools/media_killer/` 包内所有文件**：不做任何修改，保持现状，仅作为参考。
- **其它包**（`cx_tools`、`cx_wealthy`、`media_scout` 等）：除非发现阻塞性 bug，否则不修改。需要的能力通过 import 使用，或在 media_killer 内部实现。
- **`cx-studio` 中除 `cx_file_info_cache.py` 以外的文件**：不修改。

### 1.3 为什么不修改其它文件

- 旧版 `media_killer` 将逐步被 `media_killer` 替代，旧包不应再投入修改成本。
- `cx_wealthy`、`media_scout` 等共享能力已经或应当独立演进，media_killer 应作为消费者使用它们，而不是反向侵入。
- 本次范围聚焦于 media_killer 自身与 FileInfoCache 重新设计，避免扩散导致不可控的回归。

---

## 2. 可直接复制并沿用的旧版文件

### 2.1 结论

**没有任何旧版 `.py` 文件可以直接复制。**

所有旧版 Python 文件都至少存在以下一个问题，导致不能直接沿用：

- 依赖旧版 `cx_wealth`，而新版必须使用 `cx_wealthy`。
- 依赖旧版 `AppEnv` / `appenv` 全局对象，而新版 `AppEnv` 走 `IAppEnvironment` 接口。
- 依赖旧版 `Mission` / `Preset` 数据结构，而新版数据模型已重新设计。
- 依赖旧版 `Box` 透传、动态属性等模式，而新版使用强类型 dataclass。
- UI 输出策略已改变（say/whisper 分层、主题字段 `cx.mk.*`）。

### 2.2 可直接复制的非代码文件

以下资源文件内容基本稳定，可直接复制到 `media_killer/` 包中，必要时做轻微调整：

| 旧版文件 | 新版目标位置 | 复制说明 |
|---|---|---|
| `media_killer/banner.txt` | `media_killer/banner.txt` | banner 艺术字，内容不变；渲染时改用 `cx.mk.banner` 主题字段。 |
| `media_killer/help.md` | `media_killer/help.md` | 帮助文档正文，内容可直接沿用；渲染组件改用 `WealthyHelp`。 |
| `media_killer/help.en_US.md` | `media_killer/help.en_US.md` | 英文帮助文档正文，同上。 |
| `media_killer/example_preset.toml` | `media_killer/example_preset.toml` | 示例预设文件，可直接沿用；若新版 Preset schema 有变则同步调整。 |

### 2.3 复制后的检查项

- [ ] 确认资源文件路径已更新为 `media_killer.*` 包内引用。
- [ ] 确认 `banner.txt` 未包含旧版 import 或代码引用。
- [ ] 确认 `help.md` / `help.en_US.md` 中的 markup 与新版 `WealthyHelp` 兼容。
- [ ] 确认 `example_preset.toml` 符合新版 Preset schema。

---

## 3. 旧版代码参考价值与层级

旧版代码**不是实现蓝图**，只在以下层级上有参考价值：

| 参考层级 | 含义 | 使用方式 |
|---|---|---|
| **逻辑** | 业务规则、决策点、流程顺序、边界条件 | 理解旧版为什么这样做，在新版中按新设计复现正确行为 |
| **结构** | 类/函数分解、模块边界、数据流 | 参考旧版如何拆分职责，但按新版包结构重新组织 |
| **算法** | 具体计算/排序/替换/解析规则 | 提取算法思想，用新数据模型重新实现 |
| **代码** | 具体代码片段、正则、SQL、命令模板 | 仅在语义完全不变且与新架构兼容时局部复用 |

### 3.1 高参考价值文件

以下文件在**逻辑**和**算法**层面参考价值最高，需重点阅读，但**不可复制代码**。

#### `media_killer/components/mission.py`

- **逻辑**：Mission 包含哪些字段、如何标识一个 Mission、如何生成 Mission 名称。
- **结构**：Mission 作为值对象的核心结构。
- **算法**：`__rich_label__` / `__rich_detail__` 的片段组织方式。
- **代码**：`M` 标识、颜色组合、输入输出数量显示等视觉元素需迁移到新版 `cx.mk.*` 主题字段，不可直接复制。

#### `media_killer/components/mission_maker.py`

- **逻辑**：如何根据 Preset 和源文件生成 Mission，覆盖 `-y/-n` 的处理方式。
- **算法**：Mission 生成算法、路径计算、标签变量注入顺序。
- **参考要点**：标签变量依赖 `MediaDB` 元数据的时机；输出目录与目标文件名的组合规则。

#### `media_killer/components/mission_arranger.py`

- **逻辑**：去重规则、排序规则。
- **算法**：按 `source` / `preset` / `target` / `x` 排序的具体实现。
- **参考要点**：去重键应为 `(source, preset_id)`；排序规则沿用旧版。

#### `media_killer/components/mission_runner.py`

- **逻辑**：单 Mission 执行流程、临时文件机制、覆盖判断、失败处理。
- **结构**：Executor 与外部调用者的交互方式。
- **算法**：FFmpeg 命令构建、临时文件命名、进度解析。
- **参考要点**：临时文件前缀机制 `mk2tmp.<target>`、何时提交 garbage、FFmpeg 不再传 `-y/-n`。

#### `media_killer/components/mission_master.py`

- **逻辑**：批量调度、两段式中断、进度聚合。
- **算法**：并发控制、任务取消时机、总进度计算。
- **参考要点**：第一次中断只停止接新任务，第二次中断取消正在运行的任务；结果行输出时机。

#### `media_killer/components/preset.py`

- **逻辑**：Preset 的字段定义、默认值、验证规则。
- **结构**：Preset 作为配置对象的数据模型。
- **参考要点**：哪些字段必须、哪些可选、硬件加速字段的语义。

#### `media_killer/components/preset_tag_replacer.py`

- **逻辑**：标签变量的语义定义。
- **算法**：标签替换顺序、嵌套标签处理、路径锚点解析时机。
- **参考要点**：`[[input]]` / `[[output]]` / `${source:...}` 等标签的替换规则。

#### `media_killer/components/source_expander.py`

- **逻辑**：源路径展开规则、项目文件处理、目录递归、后缀过滤。
- **算法**：目录遍历顺序、项目文件识别、路径去重。
- **参考要点**：项目文件解析调用 `media_scout`；SourceExpander 本身不判断文件内容。

### 3.2 中等参考价值文件

以下文件在**逻辑**或**代码片段**层面有参考价值，但大部分需要重写。

#### `media_killer/application.py`

- **逻辑**：CLI 整体流程、命令分发、错误处理、模式组合。
- **结构**：Application 如何组合 AppEnv、AppContext、Scheduler。
- **代码**：不可直接复用，因为 UI 组件和 AppEnv 接口都已变。

#### `media_killer/appcontext.py`

- **逻辑**：命令行参数定义、`-y/-n/-c/-s/-d` 等选项的语义。
- **代码**：argparse 的参数定义列表可以参考，但解析后的上下文结构需按新版 `AppContext` 重新设计。

#### `media_killer/appenv.py`

- **逻辑**：全局 console、say/whisper、debug 模式、中断处理、生命周期。
- **结构**：AppEnv 作为上下文管理器。
- **代码**：不可复用，新版 `AppEnv` 需基于 `IAppEnvironment` 接口并注入 `cx.mk.*` 主题。

#### `media_killer/components/exception.py`

- **逻辑**：有哪些异常类型、各自的错误信息。
- **代码**：异常类名和错误消息字符串可以复用，但异常体系可按需精简。

#### `media_killer/components/mission_xml.py`

- **逻辑**：Mission 列表持久化格式（continue 功能）。
- **算法**：XML 序列化/反序列化结构。
- **代码**：XML 节点结构可参考，但字段名需匹配新版 `Mission` dataclass。

#### `media_killer/components/script_maker.py`

- **逻辑**：脚本输出格式、batch/shell 区别。
- **算法**：命令转义、脚本头生成。
- **代码**：转义逻辑可参考，但命令生成需基于新版 `MissionExecutor` 的算法。

#### `packages/cx-studio/cx_studio/filesystem/cx_file_info_cache.py`

- **逻辑**：按文件路径缓存、基于 mtime 失效、LRU 淘汰。
- **结构**：`FileInfoCache` 类的职责边界。
- **算法**：SQL 表结构、LRU SQL、单条 mtime 校验。
- **代码**：SQLite 操作可参考，但生命周期改为 `connect()`/`close()`，去掉 `__del__`，对外 API 改为 `get/set/invalidate/close`。

### 3.3 低参考价值文件

以下文件因新版设计变化较大，参考价值较低，只在快速了解旧行为时扫读即可。

#### `media_killer/mk_help_info.py`

- 新版改用 `cx_wealthy.WealthyHelp`，旧版 `WealthHelp` 包装逻辑不再适用。
- 帮助文档正文（`help.md`）仍有价值，见 §2.2。

#### `media_killer/components/input_scanner.py`

- 新版输出策略已改为 say/whisper 分层，且使用 `cx_wealthy` 组件，旧版逐行输出路径的方式不再适用。

#### `media_killer/components/argument_group.py`

- 新版 `Mission` 直接存储扁平化的 `list[str]` 选项，`ArgumentGroup` 内部结构不再需要。

#### `media_killer/__init__.py` / `media_killer/components/__init__.py`

- 仅旧版符号导出，新版包结构完全不同，无直接参考价值。

---

## 4. 新版文档权威性说明

### 4.1 以新版文档为准

以下文档是本次重构的**唯一权威依据**，实现必须遵循：

| 文档 | 作用 |
|---|---|
| [CLI_BEHAVIOR.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/CLI_BEHAVIOR.md) | 锚定所有用户可见行为：参数、路径锚点、执行流程、中断、输出。 |
| [ARCHITECTURE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md) | 包结构、模块职责、类接口、数据流、公开/私有边界。 |
| [MEDIA_PROBER_AND_CACHE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md) | FileInfoCache / MediaProber / MediaDB 的设计。 |
| [OUTPUT_AND_UI.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/OUTPUT_AND_UI.md) | 输出策略、组件选择、主题字段 `cx.mk.*`、Progress 与 Mission 标识行设计。 |
| [REFERENCE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/REFERENCE.md) | 旧版行为参考，用于理解原始需求。 |

### 4.2 旧版代码的定位

旧版代码只回答两个问题：

1. **旧版做了什么？** —— 用于验证新版设计是否遗漏功能。
2. **旧版为什么这样做？** —— 用于理解行为背后的约束，避免在新版中引入偏差。

旧版代码**不回答**以下问题：

1. 新版应该怎么组织代码？ → 看 [ARCHITECTURE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md)。
2. 新版应该输出什么？ → 看 [OUTPUT_AND_UI.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/OUTPUT_AND_UI.md) 和 [CLI_BEHAVIOR.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/CLI_BEHAVIOR.md)。
3. 新版应该怎么处理并发/缓存/路径？ → 看 [ARCHITECTURE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md) 和 [MEDIA_PROBER_AND_CACHE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/MEDIA_PROBER_AND_CACHE.md)。

### 4.3 当旧版行为与新版文档冲突时

- **默认以新版文档为准**。
- 若新版文档明显遗漏或矛盾，先暂停实现，回到文档本身澄清，而不是回退到旧版代码。
- 若旧版行为中某个细节在新版文档中未明确，应将该细节作为待澄清项提出，而不是直接沿用旧版实现。

---

## 5. 重构方式声明

### 5.1 不是"照着原来的重组成新的"

本次重构的性质是：

- **重新设计**：基于新文档重新设计数据模型、模块边界、生命周期、输出策略。
- **重新实现**：根据新设计编写代码，而不是把旧代码搬进新目录结构。
- **行为等价**：用户可见的功能和行为必须与旧版一致（以新版文档为准）。

### 5.2 允许的不同

新版实现可以在以下方面与旧版不同：

- 包结构、模块名、类名、函数签名。
- UI 组件选用（`cx_wealthy` 替代 `cx_wealth`）。
- 数据模型（强类型 dataclass 替代 `Box` / 动态 dict）。
- 内部数据流（事件驱动替代直接调用 appenv）。
- 主题与样式表达方式（`cx.mk.*` 主题字段替代硬编码颜色）。

### 5.3 不允许的偏差

新版实现**不能**在以下方面与旧版不同：

- 命令行参数和选项语义。
- 路径锚点解析规则。
- Mission 去重与排序规则。
- 临时文件命名与覆盖行为。
- 两段式中断行为（第一次停止接新任务，第二次取消正在运行的任务）。
- 用户可见的输出内容、时机和格式（以 [OUTPUT_AND_UI.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/OUTPUT_AND_UI.md) 为准）。
- continue 文件格式兼容性（沿用 XML）。

---

## 6. 实施建议

### 6.1 推荐实施顺序

1. `cx_studio/filesystem/cx_file_info_cache.py` 重新设计。
2. `media_killer/prober/`（MediaInfo / MediaProber / MediaDB）。
3. `media_killer/mission/`（Mission / InputSpec / OutputSpec）。
4. `media_killer/executor/`（MissionExecutor / MissionResult / events）。
5. `media_killer/preset/`（Preset / Loader / TagReplacer / MissionMaker）。
6. `media_killer/source/expander.py`（SourceExpander）。
7. `media_killer/persistence/mission_store.py`（MissionStore）。
8. `media_killer/script/script_maker.py`（ScriptMaker）。
9. `media_killer/scheduler/scheduler.py`（MissionScheduler）。
10. `media_killer/theme.py`、资源文件复制、`appenv.py`、`appcontext.py`、`application.py`。
11. `mk_help_info.py`、入口 `__main__.py`、测试与联调。

### 6.2 每步检查点

每完成一个模块后，应能回答：

- 该模块的公开接口是否符合 [ARCHITECTURE.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/ARCHITECTURE.md)？
- 该模块是否不依赖 `cx_wealth`、旧版 `AppEnv` 或旧版 `Mission`？
- 该模块的输出/行为是否符合 [CLI_BEHAVIOR.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/CLI_BEHAVIOR.md) 和 [OUTPUT_AND_UI.md](file:///d:/workspace/cx-studio-tk/packages/cxalio-studio-tools/media_killer/OUTPUT_AND_UI.md)？
- 是否只修改了本文件规定的范围（`media_killer/` + `cx_file_info_cache.py`）？

---

## 7. 已确认与待澄清

### 7.1 已确认

- 修改范围仅限 `media_killer/` 包 + `cx_file_info_cache.py`。
- 旧版 `.py` 文件均不直接复制。
- 资源文件 `banner.txt`、`help.md`、`help.en_US.md`、`example_preset.toml` 可直接复制。
- 新版设计文档具有最高权威。

### 7.2 待澄清（实现前必须确认）

- `help.md` / `help.en_US.md` 中是否存在与新版 `WealthyHelp` 不兼容的 markup 或占位符？
- `example_preset.toml` 是否需要根据新版 Preset schema 调整字段名？
- 旧版 `media_killer` 中是否还有未被设计文档覆盖的资源文件（如多语言、测试媒体等）？
