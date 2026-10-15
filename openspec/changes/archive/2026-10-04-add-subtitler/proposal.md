# Proposal

## Why

工具包目前没有任何字幕能力。本变更补上两块基础：一套以 **Project / Sequence / Item** 为骨架的字幕模型（Item 是可独立存在的普通对象；Sequence 与 Project 是对 Item 引用的两种编排——序列级排列与工程级组织），以及以 `subtitler`（字幕格式转换工具）作为模型第一个消费者的格式转换闭环。时间域已有 `CxTime`/`TimeRange` 资产，模型直接建立其上。

## What Changes

- **新增字幕模型**（`subtitler.common.model`）：
  - **Item** = `TimeRange` + 台词 + 说话人 + 扩展位（`extra` dict）——普通对象，独立存在，不属于任何容器；容器持引用，传输无特殊处理
  - **Sequence** = Item 的排列容器：add 自动寻找合适位置插入、尽量保证时序；读取（查询/迭代）恒依时序，且是活视图（Item 时间改写后下一次读取反映新时序）
  - **Project** = Sequence 的容器 + 元数据机制 + Item 级读取面：add 按各 Sequence 的排列顺序路由——寻找能不交叠容纳该 Item 的位置，无处可容则自动新增 Sequence；全部 Item 可时序迭代、可直接定位实例
  - 元数据不设预设字段，只留机制（通用 dict），消费由调用者或 Loader/Saver 自行处理
  - 交叠在容器中合法存在（Sequence.add 无检查）；去交叠 = 把 Items 再喂给新 Project 的 add 入口——重组即数据流，无专门算法
  - 模型不存序号、不解释任何扩展内容
- **新增格式框架**（`subtitler.common`）：Loader/Saver 两个契约 + TimeCodec 共享工具 + Format 身份对象。**语法与输出组织都归格式本体**：Loader 从来源提取 Items（不知道任何容器的存在；一次导入涉及的来源数由格式规范决定）；Saver 收到 Item 集合，单文件还是多文件、交叠如何处理是它自己的事；框架不持有格式知识的执行权，无约束声明机制
- **新增 `subtitler` CLI 工具**：字幕格式转换器——Loader 提取 Items → `Project.add` 逐个路由 → save 产出 1..N 个输出文件；工具对字幕内容无操作语义，只搬运模型
- **前台/后台分界**：字幕能力承载于 `subtitler` 工具包的 **`common` 层**（模型、Loader/Saver 契约、engine、格式实现），可被其它工具 import 复用；前台装配与 `components/` 隔离在 CLI 侧，注册接线绑定 CLI 工具本身
- **格式**：SRT、TTML、CSV 三个，每个均支持读与写
- **调整 `ITimeRange.is_overlapped_with` 判定语义**：闭区间 → 严格交叠（端点相触不视为交叠）——该方法仓库内无既有调用者，Project 路由与 Saver 分组都依赖它（详见 design D10）
- 导入导出内容对称（顺序不作等价判据）；不对称仅表现为 Saver 自主组织的多文件输出

## Capabilities

### New Capabilities

- `subtitle-model`: 字幕模型——Item 的原子地位（独立存在的普通对象）、Sequence 的排列容器语义（尽力时序插入 + 依时序读取视图）、Project 的组织语义（不交叠路由、自动增列、元数据机制、Item 级读取面）、容器间引用传输、交叠合法性
- `subtitle-formats`: 字幕格式框架——Loader/Saver 契约（语法提取与输出组织都归格式本体）、TimeCodec 共享工具、Format 身份对象、多文件命名与编码约定、格式扩展方式
- `subtitler`: 字幕格式转换 CLI 工具——转换管线（Loader → Project.add → save）、前台装配、多输出文件行为

### Modified Capabilities

- `cx-studio`：`ITimeRange.is_overlapped_with` 的交叠判定由闭区间语义调整为严格交叠（端点相触不视为交叠）。仓库内该方法无既有调用者；字幕模型的 Project 路由以相邻衔接（首尾相接）为合法常态，闭区间语义会把正常衔接的片段错误拆开。字幕模型对 `TimeRange` 存储结构本身（start+duration、end 派生）的复用不构成变更。

## Impact

- **代码**：`cxalio-studio-tools` 下新增 `subtitler` 一个工具包——`common/` 承载字幕能力（模型、Loader/Saver 契约与 engine、`common/formats` 三格式实现，作为对外提供面开放给其它工具 import），前台为四文件骨架 + `components/` 承载注册接线、参数与输出；`cx-studio` 的 `cx_studio.core.cx_timerange` 调整 `is_overlapped_with` 判定算法与三处 docstring
- **规格**：`openspec/specs/` 新增 `subtitle-model`、`subtitle-formats`、`subtitler` 三个能力域；`cx-studio` 域 ITimeRange 判定语义 REMOVED + ADDED
- **文档**：根 `CONTEXT.md` 相应 Domain 分区需收录新工具/新术语；工具清单变更涉及根 `AGENTS.md` 与帮助/i18n 文案
- **依赖**：无新第三方依赖；构建于既有 `cx-studio`/`cx-wealthy` 包与 `cxalio-studio-tools` 内共享框架 `cx_tools` 之上
- **格式**：SRT、TTML、CSV 三种（读 + 写）；三者对交叠的表达能力与输出组织各异（SRT 不许交叠——本工具采用的约定，SubRip 无正式规范；TTML/CSV 可表达交叠），正好覆盖格式世界的光谱
- **开放项**（design 阶段收口，已在 design.md 落定）：转换公共动作细节（序号、时间精度、编码/BOM）、多输出文件命名
