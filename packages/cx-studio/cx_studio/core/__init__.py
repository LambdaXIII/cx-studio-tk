"""core —— cx-studio 基础值对象与通用工具函数子包。

集中定义各业务模块共用的基础类型与纯函数，不依赖具体业务模块：

- 值对象：``CxTime``（毫秒时间值）、``FileSize``（文件大小，
  binary/international 两套单位制）、``Timebase``（帧率/丢帧时间基准）
- 时间区间：``ITimeRange``（抽象契约）与 ``TimeRange``（start+duration
  存储的实现），提供重叠/包含/时刻判定
- 数值区间：``NumberRange``（迭代、包含判定、百分比互转、区间映射、
  中点、钳制），支持可选边界与结果转换工厂
- 工具函数：``flatten_list``/``iter_with_separator``/``split_to_two``
  （序列处理）、``quick_clamp``/``quick_remap``（数值钳制与线性映射）

本模块仅做符号再导出（star import），具体实现见同名子模块。
"""

from .file_size import *
from .cx_time import *
from .cx_timebase import *
from .cx_timerange import *
from .number_range import *
from .quick_tools import *
from .functional_utils import *
