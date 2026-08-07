"""cx-wealth — Cxalio Rich UI 组件库。

.. deprecated:: 0.9.0
    本包已弃用，不再维护。请迁移至 ``cx-wealthy``。
"""

import warnings

__version__ = "0.9.0"
__deprecated__ = True
__deprecated_since__ = "0.9.0"
__replacement__ = "cx-wealthy"

warnings.warn(
    "cx-wealth is deprecated since v0.9.0 and will not receive further updates. "
    "Please migrate to cx-wealthy instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .common import *
from .dynamic_columns import *
from .indexed_list_panel import *
from .wealth_detail import *
from .wealth_help import *
from .wealth_label import *
