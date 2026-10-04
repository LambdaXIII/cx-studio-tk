# Spec Delta

## Purpose

定义字幕格式框架的行为契约：Loader/Saver 两个格式侧契约——语法提取与输出组织都归格式本体，各自完整自治（含自身 IO）；TimeCodec 共享工具；Format 身份对象；多输出文件的命名与写入约定；格式扩展方式。框架不认识具体格式，也不认识字幕模型的容器——只认识 Item。

## ADDED Requirements

### Requirement: Loader 从来源提取 Item，对容器一无所知

Loader MUST 从其格式规范的来源提取 Item。读取文件、判定编码、解码、语法解析均为 Loader 自己的职责；入口来源形态由契约定义（本变更三格式均为单文件路径），一次导入涉及的文件数由格式规范决定——Loader MAY 为一个入口自行读取其格式要求的关联文件。Loader MUST 只产出 Item（格式扩展字段写入扩展位，键带格式前缀），MUST NOT 感知或产出任何模型容器。提取 MUST 忠实：MUST NOT 重排、丢弃或改写来源内容；语法错误 MUST 抛 FormatError（带位置信息），MUST NOT 静默跳过或部分返回。

#### Scenario: 忠实提取

- **WHEN** Loader 解析一个含交叠序列的来源
- **THEN** 交叠 Item 原样产出，提取不失败、不丢片、不改写

#### Scenario: 对容器无知

- **WHEN** 检查 Loader 的公开接口
- **THEN** 参数与返回值只有 Item 与原始来源，无 Sequence/Project 或任何容器概念

### Requirement: Saver 自主组织输出

Saver MUST 接收 Item 集合（可迭代）与目标路径，自主决定输出的文件组织——单文件还是多文件、交叠如何处理是 Saver 自己的事（格式知识归格式本体）。多文件时 MUST 以目标 stem 加 `.part<k>` 序号后缀命名（从 1 起，按输出顺序），目录与扩展名跟随目标路径。写入前 MUST 一次性校验全部目标路径：任一已存在则报错中止且不写出任何文件、不覆盖既有文件。写出 MUST 使用 UTF-8 编码（不带 BOM）。Saver MUST 返回实际产出的路径列表。有编号格式的 Saver MUST 按其组织结果逐文件从 1、按 Item 时序写出编号字面（不沿用来源编号）。

#### Scenario: 不许交叠的格式自主拆分

- **WHEN** 向序列内部不交叠的格式（如 SRT）的 Saver 提供含交叠的 Item 集合
- **THEN** Saver 自行将 Item 组织为多个内部不交叠的输出文件，全部 Item 无丢失

#### Scenario: 允许交叠的格式单文件

- **WHEN** 向允许交叠的格式（如 TTML/CSV）的 Saver 提供含交叠的 Item 集合
- **THEN** 产出一个文件，交叠原样保留

#### Scenario: 目标已存在

- **WHEN** 任一目标输出路径（含派生的 `.part<k>` 路径）已存在
- **THEN** 报错中止，不写出任何文件，不覆盖既有文件

### Requirement: 时间的模式换算经 TimeCodec 共享工具

时间的模式驱动解析、格式化与单调取整 MUST 由框架的 TimeCodec 承载，各 Loader/Saver 取用之；各格式的时间表示模式为该格式实现内部的常量，MUST NOT 成为跨组件接口。精度取舍 MUST 保持时间顺序：换算后 Item 的先后关系 MUST NOT 因取舍而颠倒。MUST NOT 复用 CxTime 的宽松时间戳解析（其前缀匹配与末段换算语义不满足格式契约的严格性）。

#### Scenario: 严格解析

- **WHEN** 来源时间文本不符合该格式的模式
- **THEN** 抛 FormatError，不做宽松兜底

#### Scenario: 精度取舍不颠倒时序

- **WHEN** 毫秒级时间换算到精度更粗的格式（本变更的 SRT/TTML/CSV 均为毫秒级，此场景为面向未来更粗精度格式的前瞻性契约，由 TimeCodec 的单调取整逻辑承载）
- **THEN** 换算后各 Item 的先后关系与换算前一致

### Requirement: Format 打包格式身份，扩展不动核心

格式实现 MUST 以 Format 对象打包：名称、所识别的文件扩展名、Loader 与 Saver。扩展名供前台接线识别。框架与模型 MUST NOT 感知具体格式。新增格式 MUST 仅需：实现 Loader/Saver、以 Format 打包、在前台注册——框架与模型 MUST NOT 因新增格式而修改。

#### Scenario: 扩展格式不改核心

- **WHEN** 新增一个格式实现并在前台注册
- **THEN** 框架与模型代码零改动，转换流程照常工作

### Requirement: 导入导出内容对称

对不含交叠的输入，「Loader 提取 → 导出回同一格式」MUST 恢复与来源内容等价的输出——Item 的时间、台词、说话人、扩展位内容等价（顺序不作判据：来源文档排列顺序与时序不同时，以时序为准；等价以模型可承载的内容为界，来源中超出格式实现范围、未被解析入模型的结构不计入）。不对称 MUST 仅表现为 Saver 自主组织的多文件输出。

#### Scenario: 干净输入往返无损

- **WHEN** 读入一个不含交叠的 SRT 并原样导出为 SRT
- **THEN** 输出与输入在 Item 内容上等价

### Requirement: 格式框架不依赖 CLI 组件

字幕模型、Loader/Saver 契约与格式实现 MUST 位于可被其它工具 import 的 `subtitler.common` 层，MUST NOT 依赖任何 CLI 组件（appenv/context/注册接线）。

#### Scenario: 复用面

- **WHEN** 另一个工具 import 字幕模型与格式框架
- **THEN** 不引入对任何 CLI 组件的依赖
