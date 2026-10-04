# Spec Delta

## Purpose

调整 `ITimeRange.is_overlapped_with` 的交叠判定语义：由闭区间语义（端点相触视为重叠）改为严格交叠（端点相触不视为交叠）。该方法在仓库内无既有调用者；字幕框架的导出裂变以相邻衔接（首尾相接）为合法常态，闭区间语义会把正常衔接的片段错误裂开。`is_contained_by` 与 `contains_time` 的闭区间语义不变。判定场景整体改写（原「共享端点视为重叠」场景的预期反转，场景更名），故以 REMOVED + ADDED 承载。

## REMOVED Requirements

### Requirement: ITimeRange 定义时间区间的抽象契约

**Reason**: `is_overlapped_with` 的交叠判定语义由闭区间调整为严格交叠——端点相触不再视为交叠。仓库内该方法无既有调用者；字幕导出裂变以相邻衔接（首尾相接）为合法常态，闭区间语义会把正常衔接的片段错误裂开。

**Migration**: 判定调用方按新语义复核端点相触场景（相触 → 不交叠）；替代契约由 ADDED Requirement「ITimeRange 定义时间区间的抽象契约与判定语义」承载，`is_contained_by`/`contains_time` 的闭区间语义不变。

## ADDED Requirements

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
