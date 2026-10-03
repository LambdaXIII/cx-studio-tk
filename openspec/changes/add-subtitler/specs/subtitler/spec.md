# Spec Delta

## Purpose

定义 `subtitler` CLI（字幕格式转换工具）的现行行为契约：转换工作流、前台注册接线、支持的格式面、多输出文件行为与错误处理。

## ADDED Requirements

### Requirement: subtitler 是围绕字幕模型的格式转换工具

subtitler MUST 遵循 `cx_tools.app` 的三层分层与 CLI 通用生命周期（入口 `run()` → Context/Env → Application）。调用形如 `subtitler INPUT OUTPUT [-d] [-h | --tutorial]`：读入单个输入文件 → 得到一个集合 → 按目标格式写出（裂变时产出 1..N 个输出文件）。工具本身 MUST NOT 对字幕内容施加编辑、修剪、重排等操作语义——只经框架搬运模型。支持的格式 MUST 为 SRT、TTML、CSV，且 MUST 均可作源与目标；输入与目标同格式 MUST 允许（往返转换）。格式识别 MUST 按文件扩展名进行，未识别的扩展名报错中止。

#### Scenario: 转换即搬运

- **WHEN** 将一个 SRT 文件转换为目标格式
- **THEN** 片段的时间、台词与扩展字段经模型原样流转，工具不增删改片段内容；说话人等源格式无法表达的字段为空值，不被凭空生成

#### Scenario: 三格式互转

- **WHEN** 指定 SRT、TTML、CSV 中任意两者作为源与目标
- **THEN** 转换正常完成；每个格式均支持读与写

### Requirement: 注册接线绑定 CLI，框架不感知所接格式

本工具支持哪些格式 MUST 由 CLI 前台的注册接线决定；字幕模型、格式框架与适配器 MUST NOT 感知 subtitler 注册了哪些格式。注册与格式识别（含按文件扩展名确定源/目标格式适配器）MUST 位于前台组件，不入 common 层契约。

#### Scenario: 前台接线决定格式面

- **WHEN** subtitler 启动装配
- **THEN** 所支持格式由 CLI 注册表给出；common 层的框架与适配器不含对本工具格式面的引用

#### Scenario: 换一个前台接不同的格式

- **WHEN** 另一工具复用 common 层并注册不同的格式子集或超集
- **THEN** 框架与模型无需改动即可服务该工具的格式面

### Requirement: 转换异常报错中止

读入失败（文件不存在、格式解析失败、无法识别的扩展名、编码无法判定）时，subtitler MUST 报错中止，MUST NOT 写出部分或空的输出文件。导出的全部输出文件 MUST 写出成功，任一写失败 MUST 报错且 MUST 不静默继续；输出目标已存在时 MUST 报错且 MUST NOT 覆盖。

#### Scenario: 源文件解析失败

- **WHEN** 源文件存在但内容不符合其格式的语法
- **THEN** 工具报错中止，不创建任何输出文件

#### Scenario: 多输出部分失败

- **WHEN** 导出需产出多个输出文件且其中一个写入失败
- **THEN** 工具报错而非静默继续，失败情况对用户可见
