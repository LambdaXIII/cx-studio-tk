# Spec Delta

## Purpose

定义字幕模型的行为契约：Item 的原子地位（独立存在的普通对象）、Sequence 的排列容器语义（尽力时序插入、依时序读取视图）、Project 的组织语义（不交叠路由、自动增列、元数据机制、Item 级读取面）、容器间的引用传输，以及交叠的合法性。模型不认识任何字幕格式。

## ADDED Requirements

### Requirement: Item 是可独立存在的普通对象

每个 Item MUST 携带：一个时间范围（复用 `cx_studio.core` 的 `TimeRange`——以 start + duration 存储、end 派生）、台词内容、说话人、扩展位（extra dict）。时间范围之外，Item MUST NOT 冗余存储开始时间或时长。说话人为可空字段：来源格式无说话人语法时为空值。Item MUST NOT 依附于任何容器——容器持有 Item 的引用，Item 可独立创建、独立存在、跨容器流转，同一实例可同时被多个容器引用。模型 MUST NOT 解释、校验或约束扩展位内容（键的格式前缀约定由格式侧遵守）。

#### Scenario: Item 独立于容器存在

- **WHEN** 直接构造一个 Item，不加入任何容器
- **THEN** Item 完整可用；加入容器后其状态不因容器而变（引用语义）

#### Scenario: 时长由时间范围导出

- **WHEN** Item 的时间范围为起 10s、止 15s
- **THEN** 时长为 5s，且不存在重复存储的时长状态

### Requirement: Sequence 是 Item 的排列容器，读取恒依时序

Sequence 添加 Item 时 MUST 自动尝试寻找合适位置插入，尽量保证时序（实现层面行为）。Sequence 的内部排列 MUST NOT 被本规格承诺——任何时刻的排列状态无约束（Item 时间被改写后排列可能陈旧）。对外读取（迭代、查询）MUST 恒按开始时间时序给出，且 MUST 是活视图：Item 时间改写后，下一次读取 MUST 反映新时序。Sequence MUST NOT 因交叠而校验、拒绝、告警或改写。Sequence MUST NOT 暴露位置索引定位（排列非稳定句柄），MUST NOT 携带元数据或名称。

#### Scenario: 读取恒为时序

- **WHEN** 以任意顺序向 Sequence 添加 Item 后迭代
- **THEN** 迭代结果按开始时间时序

#### Scenario: 活视图

- **WHEN** 迭代之后改写某 Item 的时间范围，再次迭代
- **THEN** 迭代结果反映改写后的时序

#### Scenario: 交叠正常入列

- **WHEN** 向 Sequence 添加与既有 Item 交叠的 Item
- **THEN** 添加成功，原样共存，无告警、无改写

### Requirement: Project 将 Item 组织为不交叠的 Sequence

Project MUST 持有 Sequence 的有序集合（排列序 = 创建序）与元数据机制。Project.add(Item) MUST 按各 Sequence 的排列顺序路由：寻找能不交叠容纳该 Item 的 Sequence（交叠判定遵循 `ITimeRange.is_overlapped_with` 的严格交叠语义，端点相触不视为交叠），将 Item 插入该 Sequence 的时序位置；所有 Sequence 均无合适位置时 MUST 自动新增 Sequence。经此路径进入的 Item 使各 Sequence 内部无交叠；该性质是组织行为的结果而非校验不变量——绕过 Project.add（直接操作 Sequence、改写已入列 Item 的时间）产生的交叠 MUST 被容忍。MUST NOT 提供去交叠的特殊算法：去交叠 = 将 Item 重新喂给一个新 Project 的 add 入口。

#### Scenario: 路由分屋

- **WHEN** 向空 Project 依次添加互相交叠的 Item A、B
- **THEN** A 与 B 落入不同 Sequence，各 Sequence 内部无交叠，全部 Item 可从 Project 取得，无丢失

#### Scenario: 自动新增 Sequence

- **WHEN** 所有既有 Sequence 都无能不交叠容纳新 Item 的位置
- **THEN** Project 自动新增 Sequence 并容纳该 Item

#### Scenario: 去交叠即数据流

- **WHEN** 将一个含交叠 Sequence 的 Project 的全部 Item 迭代取出，喂给一个新 Project 的 add 入口
- **THEN** 新 Project 的各 Sequence 内部无交叠，全部 Item 无丢失；原 Project 不受影响

### Requirement: Project 与 Sequence 都可作为 Item 集合读取

Project 与 Sequence MUST 都提供 Item 级读取面：迭代（依时序——Project 为跨 Sequence 归并的全量时序）与实例身份查询（contains，按对象身份匹配）。Project MUST 另提供其 Sequence 的读取（按创建序迭代）。读取返回的 MUST 是 Item 真实实例（引用语义），Project MUST NOT 要求使用者经所属 Sequence 二跳获取 Item。容器 MUST NOT 提供 index 定位，MUST NOT 引入 id 句柄——引用本身即句柄。

#### Scenario: 双层读取

- **WHEN** 分别迭代 Project 与其任一 Sequence
- **THEN** 前者得到全量 Item 的时序流（跨 Sequence 归并），后者得到该 Sequence 的时序流

#### Scenario: 引用即句柄

- **WHEN** 持有从迭代中获得的 Item 引用
- **THEN** contains 能以该引用查询归属，take 能按同一身份取出

### Requirement: 容器间的 Item 传输为引用流转

容器 MUST 提供 add（接受单个 Item）与 add_from（接受来自任意 Item 容器的可迭代）的入向通道；Sequence 与 Project MUST 都提供 take：按实例身份将 Item 从本容器取出并脱离，返回该实例，未命中返回 None。容器间传输 = take 与 add 的组合，MUST NOT 有复制、所有权转移或其它特殊处理（依 Python 对象默认行为）。MUST NOT 提供 remove（销毁语义的减员）。

#### Scenario: take 脱离后 add 转移

- **WHEN** 将 Item 从 Sequence take 后 add 进 Project
- **THEN** 该 Item 脱离原 Sequence、被新容器持有；原容器不再含它

#### Scenario: 未命中返回 None

- **WHEN** take 一个不属于本容器的 Item
- **THEN** 返回 None，容器状态不变

### Requirement: 元数据是机制不是字段

Project MUST 持有通用 dict 元数据容器，MUST NOT 设预设字段。模型 MUST NOT 解释元数据内容；其写入与消费由调用者或格式侧自行处理，键的格式前缀约定由格式侧遵守（与 Item 扩展位同构）。Sequence MUST NOT 携带元数据。

#### Scenario: 元数据自由承载

- **WHEN** 调用者向 Project 的元数据写入任意键值
- **THEN** 模型原样持有，不解释、不校验

### Requirement: 序号不进入模型

序号是写出侧的编号字面，MUST NOT 进入模型——Item、Sequence、Project 均不存储或派生序号。

#### Scenario: 模型层无序号

- **WHEN** 以模型层公开接口执行任何操作
- **THEN** 参数与返回值不含序号字段或格式特定概念
