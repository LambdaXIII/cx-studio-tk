# cx-studio Specification

## Purpose
定义 cx-studio 基础设施库时间域值对象家族的现行行为契约：CxTime（毫秒精度时间值对象）的内部存储、构造、分解访问、算术比较、时间码与时间戳互转；Timebase（时间基准）的帧率描述与 drop_frame 推导；TimeRange（时间区间）的存储语义、区间判定与赋值语义；以及时间域资产作为核心基础设施的保护契约与公开 API 删除约束。

## Requirements

### Requirement: CxTime 是毫秒精度的不可变时间值对象

CxTime MUST 以整数毫秒为唯一内部存储（total_milliseconds 属性），入参 MUST 经 `int()` 归一。CxTime 实例 MUST 可哈希、可 copy/deepcopy（返回等值新实例）。构造 MUST 支持负值（表示零时刻之前的时长）。

#### Scenario: 从毫秒数构造并访问总时长

- **WHEN** 以 `CxTime(3661500)` 构造实例
- **THEN** `total_milliseconds` 为 3661500，`total_seconds` 为 3661.5，`total_hours` 约 1.0167

#### Scenario: 负值构造与分解

- **WHEN** 以 `CxTime(-3600001)` 构造实例
- **THEN** `total_milliseconds` 为 -3600001；`hours` 为 23（对 24 取模），`minutes` 为 59，`seconds` 为 59，`milliseconds` 为 999

#### Scenario: 整数零比较特判

- **WHEN** 对毫秒总数为 500 的 CxTime 实例执行 `== 0`
- **THEN** 结果为 False；对毫秒总数为 0 的实例执行 `== 0` 结果为 True

### Requirement: CxTime 提供全量换算与分解访问属性

CxTime MUST 提供 total_days / total_hours / total_minutes / total_seconds / total_milliseconds 五个全量换算属性（浮点或整数）。MUST 提供 days / hours / minutes / seconds / milliseconds 五个分解属性：hours 及以下属性 MUST 对 24/60 取模，不跨段进位累加。

#### Scenario: 分解属性不进位

- **WHEN** 以 `CxTime(90000000)` 构造实例（25 小时）
- **THEN** `days` 为 1，`hours` 为 1（25 % 24），`minutes` 为 0，`seconds` 为 0，`milliseconds` 为 0

### Requirement: CxTime 的算术与比较运算

CxTime MUST 支持加法（CxTime + CxTime）、减法（CxTime - CxTime）、乘法（CxTime × int/float）、除法（CxTime ÷ int/float，结果 round 取整），均返回新 CxTime 实例。类型不符 MUST 抛出 NotImplementedError。比较运算 MUST 支持 CxTime 之间的逐毫秒比较，以及与整数 0 的特判比较（`0` 视作零时长）；与非 CxTime、非零整数类型比较 MUST 抛出 NotImplementedError。

#### Scenario: 乘法缩放

- **WHEN** 对 `CxTime(1000)` 执行 `* 2.5`
- **THEN** 结果为 `CxTime(2500)`

#### Scenario: 除法取整

- **WHEN** 对 `CxTime(1500)` 执行 `/ 2`
- **THEN** 结果为 `CxTime(750)`（round 取整）

#### Scenario: 不兼容类型运算抛出异常

- **WHEN** 对 CxTime 实例执行 `+ "hello"`
- **THEN** 抛出 NotImplementedError

### Requirement: CxTime 支持多种构造方式

CxTime MUST 提供以下类方法构造方式：`from_milliseconds(int)`、`from_seconds(float)`、`from_minutes(float)`、`from_hours(float)`、`from_days(float)`（浮点入参 MUST 经 × 对应基数后 round 取整归一为毫秒），以及 `zero()`（零时长）和 `one_second()`（1000 毫秒）快捷构造。

#### Scenario: 从秒数构造

- **WHEN** 执行 `CxTime.from_seconds(1.5)`
- **THEN** 得到的实例 `total_milliseconds` 为 1500

#### Scenario: zero 与 one_second

- **WHEN** 分别调用 `CxTime.zero()` 和 `CxTime.one_second()`
- **THEN** 两者 `total_milliseconds` 分别为 0 和 1000

### Requirement: CxTime 的 pretty_string 格式化

CxTime 实例的 `pretty_string` 属性 MUST 自大到小拼接日/小时/分/秒各段，仅输出数值非零的段，段间无分隔符，单位文字经 i18n 翻译。毫秒段仅在毫秒余数非零且总时长为负时附加输出。若所有段均为零（正数且不足 1 秒）MUST 返回空字符串。

#### Scenario: 正数时长格式化

- **WHEN** 对 `CxTime(3661000)` 访问 `pretty_string`
- **THEN** 结果为 `1小时1分1秒`（i18n 源语言中文，具体显示取决于当前 locale）

#### Scenario: 不足一秒的正数返回空串

- **WHEN** 对 `CxTime(500)` 访问 `pretty_string`
- **THEN** 结果为空字符串

### Requirement: CxTime 的时间戳格式化与解析

CxTime MUST 支持 `HH:MM:SS.mmm` 格式的时间戳互转。`to_timestamp()` 输出时/分/秒各两位（取自分解属性，对 24/60 取模）加毫秒三位补零。`from_timestamp(ts)` 使用正则 `(\d{2}):(\d{2}):(\d{2})[:;.,](\d+)` 前缀匹配解析，末段数字直接作为毫秒值（不按三位补零换算）。格式不匹配 MUST 抛出 ValueError。

#### Scenario: 时间戳往返一致性

- **WHEN** 构造 `CxTime(3723456)` 后调用 `to_timestamp()` 再用 `from_timestamp()` 解析
- **THEN** 解析结果的 `total_milliseconds` 与原实例相等

#### Scenario: 格式非法抛出 ValueError

- **WHEN** 调用 `CxTime.from_timestamp("not a timestamp")`
- **THEN** 抛出 ValueError

### Requirement: CxTime 的时间码格式化与解析

CxTime MUST 支持与 Timebase 配合的时间码互转。`to_timecode(timebase)` 的帧号按 `round(milliseconds / 1000 × fps)` 换算，帧分隔符在 timebase.drop_frame 为 True 时用 `;` 否则用 `:`，帧号 MUST 补零到 fps 十进制位数。`from_timecode(tc, timebase)` 末段数字按帧数处理并换算为毫秒 `round(frames / fps × 1000)`。drop_frame 不影响换算本身，仅决定帧分隔符。格式不匹配 MUST 抛出 ValueError。

#### Scenario: 时间码往返一致性

- **WHEN** 以 Timebase(fps=24) 将 `CxTime(41708)` 转为时间码再解析回来
- **THEN** 解析结果 `total_milliseconds` 与原实例相等

#### Scenario: drop_frame 仅影响分隔符

- **WHEN** 以 Timebase(fps=30, drop_frame=True) 将 `CxTime(1000)` 转为时间码
- **THEN** 输出的帧分隔符为 `;` 而非 `:`，帧数值与 drop_frame=False 时一致

### Requirement: Timebase 描述帧率与丢帧标记

Timebase MUST 以整数 fps（每秒帧数）和布尔 drop_frame 描述时间基准。`from_fps(x)` 类方法 MUST 对入参四舍五入为整数 fps，当入参与取整结果不一致时（即入参含小数，如 29.97）自动将 drop_frame 置为 True，否则为 False。Timebase MUST 提供 `milliseconds_per_frame` 属性，值为 `round(1000 / fps)`。

#### Scenario: 小数帧率自动启用 drop_frame

- **WHEN** 调用 `Timebase.from_fps(29.97)`
- **THEN** 返回的 Timebase 的 `fps` 为 30，`drop_frame` 为 True，`milliseconds_per_frame` 为 33

#### Scenario: 整数帧率不启用 drop_frame

- **WHEN** 调用 `Timebase.from_fps(24)`
- **THEN** `fps` 为 24，`drop_frame` 为 False，`milliseconds_per_frame` 为 42

### Requirement: ITimeRange 定义时间区间的抽象契约与判定语义

ITimeRange MUST 定义 start、end、duration 三个抽象属性（均为 CxTime），并提供三个判定方法：`is_overlapped_with(other)` 判定两区间是否交叠（严格交叠语义：`self.start < other.end and self.end > other.start`；端点相触——一区间的终点恰为另一区间的起点——不视为交叠），`is_contained_by(other)` 判定本区间是否完全包含于另一区间，`contains_time(time)` 判定时刻是否落在区间内（闭区间：`start <= time <= end`）。

#### Scenario: 区间交叠判定不含端点相触

- **WHEN** 区间 A 为 [100, 200]，区间 B 为 [200, 300]
- **THEN** `A.is_overlapped_with(B)` 返回 False（共享端点不视为交叠）

#### Scenario: 区间真交叠仍判定为交叠

- **WHEN** 区间 A 为 [100, 250]，区间 B 为 [200, 300]
- **THEN** `A.is_overlapped_with(B)` 返回 True

#### Scenario: 时刻包含含边界

- **WHEN** 区间为 [100, 300]，判定时刻 100 是否包含
- **THEN** `contains_time(CxTime(100))` 返回 True

### Requirement: TimeRange 以 start+duration 存储并维持恒等关系

TimeRange MUST 以 start 和 duration 两个 CxTime 存储，end MUST 为只读派生属性 `start + duration`。三者关系恒为 `end == start + duration`。赋值语义：写 start 或 duration 直接替换对应内部值；写 end MUST 反向推导时长并更新 duration（`duration = end - start`），从而维持恒等关系。相等判定 MUST 仅比较 start 与 duration，与 ITimeRange 子类型比较按此规则，与非 ITimeRange 类型比较返回 NotImplemented。

#### Scenario: 赋值 end 维持恒等

- **WHEN** 构造 TimeRange(start=CxTime(0), duration=CxTime(1000)) 后执行 `end = CxTime(3000)`
- **THEN** `duration` 变为 CxTime(3000)，`end` 仍等于 start + duration

#### Scenario: 赋值 start 更新 end 但保持 duration

- **WHEN** 构造 TimeRange(start=CxTime(0), duration=CxTime(1000)) 后执行 `start = CxTime(500)`
- **THEN** `duration` 仍为 CxTime(1000)，`end` 变为 CxTime(1500)

#### Scenario: 相等判定

- **WHEN** 两个 TimeRange 的 start 和 duration 均相等
- **THEN** 两者判等为 True；仅 duration 不同则为 False

### Requirement: 时间域代码资产保护

cx-studio 包中的时间域代码（CxTime、Timebase、TimeRange 及其关联的时间码/时间戳处理逻辑）MUST 作为核心资产保留，MUST NOT 以仓库内零引用为由删除。仓库内引用数 MUST NOT 作为判定时间域代码为死代码的唯一依据，原因在于 cx-studio 是开放功能库，外部消费者对仓库不可见。

#### Scenario: 零引用不得作为删除依据

- **WHEN** cx-studio 包内某个时间域类（如 TimeRange）在仓库内无任何直接引用
- **THEN** 该类 MUST NOT 被判定为死代码或据此删除

### Requirement: 公开 API 删除须经作者确认

删除 cx-studio 包的任何公开 API 前 MUST 获得该 API 作者的确认，确认内容为该 API 不可用、未完成或未文档化。MUST NOT 在未经确认的情况下删除公开 API。

#### Scenario: 删除公开 API 前的确认

- **WHEN** 需要删除 cx-studio 包的某个公开 API
- **THEN** 必须先获得该 API 作者确认其不可用/未完成/未文档化，确认后方可删除
