# Proposal

## Why

工具包目前没有任何字幕能力，而字幕工作（转换、后续的编辑/质检等）都应围绕一套统一的字幕模型进行——仓库时间域已有 `CxTime`/`TimeRange` 资产，但其上从未建过字幕模型。本变更补上这块基础：以 `subtitler`（字幕格式转换工具）作为模型的第一个消费者，打通模型的读写闭环。

## What Changes

- **新增字幕模型**（后台基础，所有字幕工作的中心）：
  - 片段（segment）= `TimeRange` + 台词（text） + 说话人（speaker） + 扩展位（开放字段，容纳格式私货与未来生长）
  - 时序由各片段的开始时间定义——顺序是片段的属性，不是容器的排列
  - 集合（collection）= 片段的集合，模型一等公民；实现按 start 插入维持有序，读取恒为时序；交叠是合法状态，模型不校验、不拒绝
  - 作品 = 集合 ×N，显式组织（手动划分或导入时解析），无隐式推断
  - 模型不引用「序列」概念——序列是格式侧的产物
- **新增 `subtitler` CLI 工具**：字幕格式转换器，构建在 `cx_tools.app` 三层分层之上，工作流为「读入（源格式，单文件 → 单集合）→ 模型 → 写出（目标格式，按约束产出 1..N 个输出文件）」——模型的作品（集合 ×N）是模型层能力，本工具单次调用读入单个文件；工具本身对字幕内容无操作语义，只搬运模型
- **新增格式框架（可扩展的适配器结构）**：框架定义适配器接口契约（SPI），各格式以实现形式接入；**语法归适配器**（序列 ↔ 片段的 parse/serialize，含格式私货字段读写与所认扩展名的声明），**语义归框架**（导入时序列 1:1 落集合、导出时按适配器声明的约束决定是否把含交叠的集合裂变为 1..N 个序列、序号重编、时间精度换算）；格式自身的约束（如 SRT 序列不许交叉）以声明形式交给框架统一执行，不上溯模型、不散落各适配器
- **前台/后台分界**：字幕能力承载于 `subtitler` 工具包的 **`common` 层**——集合模型与 Loader/Saver 契约（含 engine）在 `subtitler.common` 包本体，具体格式实现于 `subtitler.common.formats`（common 层是工具的对外提供面，可被其它工具 import 复用）；前台装配与 `components/` 隔离在 CLI 侧，**注册接线绑定 CLI 工具本身**——本工具接哪些格式是前台装配决策，能力层对此一无所知
- **格式适配器**：SRT、TTML、CSV 三个，每个均支持读与写
- 导入无异常（无交叠输入）时导入导出对称、往返无损；不对称仅出现在交叠裂变的异常路径
- **调整 `ITimeRange.is_overlapped_with` 判定语义**：闭区间 → 严格交叠（端点相触不视为交叠）——该方法仓库内无既有调用者，调整后导出裂变分组直接复用它（详见 design D10）
- 确立在既有时间资产上：时间原语直接复用 `cx_studio.core` 的 `CxTime`/`TimeRange`，不新造时间类型

## Capabilities

### New Capabilities

- `subtitle-model`: 字幕模型——片段结构（TimeRange + 预置字段 + 扩展位）、时序语义（由 start 定义）、集合作为片段集合的组织单位、交叠合法性、作品的多集合结构
- `subtitle-formats`: 字幕格式框架——适配器接口契约（语法归适配器：序列 ↔ 片段的解析/序列化与格式约束声明）、语义归框架（导入 1 序列→1 集合、导出按声明约束裂变 1..N 序列、编号重编、精度换算）、格式扩展方式（新增格式不动框架与模型）
- `subtitler`: 字幕格式转换 CLI 工具——前台装配（注册接线：本工具接哪些格式）、转换工作流、多输出文件行为

### Modified Capabilities

- `cx-studio`：`ITimeRange.is_overlapped_with` 的交叠判定由闭区间语义调整为严格交叠（端点相触不视为交叠）。仓库内该方法无既有调用者；字幕导出裂变以相邻衔接（首尾相接）为合法常态，闭区间语义会把正常衔接的片段错误裂开。字幕模型对 `TimeRange` 存储结构本身（start+duration、end 派生）的复用不构成变更。

## Impact

- **代码**：`cxalio-studio-tools` 下新增 `subtitler` 一个工具包——`common/` 承载字幕能力（集合模型、Loader/Saver 契约与 engine、`common/formats` 三格式实现，作为对外提供面开放给其它工具 import），前台为四文件骨架 + `components/` 承载注册接线、参数与输出；`cx-studio` 的 `cx_studio.core.cx_timerange` 调整 `is_overlapped_with` 判定算法与三处 docstring
- **规格**：`openspec/specs/` 新增 `subtitle-model`、`subtitle-formats`、`subtitler` 三个能力域；`cx-studio` 域 ITimeRange 判定语义 MODIFIED
- **文档**：根 `CONTEXT.md` 相应 Domain 分区需收录新工具/新术语；工具清单变更涉及根 `AGENTS.md` 与帮助/i18n 文案
- **依赖**：无新第三方依赖；构建于既有 `cx-studio`/`cx-wealthy` 包与 `cxalio-studio-tools` 内共享框架 `cx_tools` 之上
- **格式**：SRT、TTML、CSV 三种适配器（读 + 写）；三者交叠约束各异（SRT 序列不许交叠——本工具采用的约定，SubRip 无正式规范；TTML/CSV 可表达交叠），共同覆盖框架「约束声明 + 统一执行」结构的约束光谱
- **开放项**（design 阶段收口，已在 design.md 落定）：转换公共动作细节（序号重编、时间精度取舍、编码/BOM）、多输出文件命名规则
