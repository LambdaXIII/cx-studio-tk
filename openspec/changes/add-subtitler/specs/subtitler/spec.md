# Spec Delta

## Purpose

定义 `subtitler` CLI（字幕格式转换工具）的现行行为契约：转换管线、前台注册接线、支持的格式面、多输出文件行为与错误处理。

## ADDED Requirements

### Requirement: subtitler 是围绕字幕模型的格式转换工具

subtitler MUST 遵循 `cx_tools.app` 的三层分层与 CLI 通用生命周期（入口 `run()` → Context/Env → Application）。调用形如 `subtitler INPUT OUTPUT [-d] [-h | --tutorial]`。转换管线：Loader 从输入文件提取 Item → 逐个 `Project.add` 路由组织 → 将 Project 的 Item 集合交给目标格式的 Saver → Saver 自主组织并写出 1..N 个输出文件。工具本身 MUST NOT 对字幕内容施加编辑、修剪、重排等操作语义——只搬运模型。支持的格式 MUST 为 SRT、TTML、CSV，且 MUST 均可作源与目标；输入与目标同格式 MUST 允许（往返转换）。格式识别 MUST 按文件扩展名进行，未识别的扩展名报错中止。

#### Scenario: 转换即搬运

- **WHEN** 将一个 SRT 文件转换为目标格式
- **THEN** Item 经 Loader → Project → Saver 原样流转，工具不增删改内容；源格式无法表达的字段为空值，不被凭空生成

#### Scenario: 交叠来源转不交叠格式

- **WHEN** 输入 SRT 含交叠序列，目标为 SRT
- **THEN** 产出多个内部不交叠的输出文件（`.part<k>` 按输出顺序），全部 Item 无丢失

#### Scenario: 交叠来源转允许交叠格式

- **WHEN** 输入 SRT 含交叠序列，目标为 TTML
- **THEN** 产出单个文件，交叠原样保留

#### Scenario: 相邻衔接不拆分

- **WHEN** 来源含端点相触（如 [0,5s] + [5,10s]）的相邻 Item，目标为 SRT
- **THEN** 不因此拆分输出（端点相触不构成交叠）

### Requirement: 注册接线绑定 CLI，框架不感知所接格式

本工具支持哪些格式 MUST 由 CLI 前台的注册接线决定；字幕模型、Loader/Saver 契约与格式实现 MUST NOT 感知 subtitler 注册了哪些格式。注册与格式识别（含按文件扩展名确定源/目标格式）MUST 位于前台组件，不入 `subtitler.common` 层契约。

#### Scenario: 前台接线决定格式面

- **WHEN** subtitler 启动装配
- **THEN** 所支持格式由 CLI 注册表给出；`subtitler.common` 不含对本工具格式面的引用

#### Scenario: 换一个前台接不同的格式

- **WHEN** 另一工具复用 `subtitler.common` 层并注册不同的格式子集或超集
- **THEN** 框架与模型无需改动即可服务该工具的格式面

### Requirement: 转换异常报错中止

读入失败（文件不存在、编码无法判定、格式语法错误、未识别的扩展名）时，subtitler MUST 报错中止，MUST NOT 写出部分或空的输出文件。导出的全部输出文件 MUST 写出成功，任一写失败 MUST 报错且 MUST NOT 静默继续；输出目标已存在时 MUST 报错且 MUST NOT 覆盖。

#### Scenario: 源文件解析失败

- **WHEN** 源文件存在但内容不符合其格式的语法
- **THEN** 工具报错中止，不创建任何输出文件

#### Scenario: 多输出部分失败

- **WHEN** 导出需产出多个输出文件且其中一个写入失败
- **THEN** 工具报错而非静默继续，失败情况对用户可见
