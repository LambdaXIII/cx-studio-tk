# 已知例外：模块级工具函数保留 appenv 单例导入

hosts_keeper 的 `hosts_saver.py` 中，`_elevated_replace_*` 和 `_dns_flush_*` 是模块级函数，通过 CrossRunner 装饰器注册，签名固定为 `(source, target) -> bool` 或 `(skip_flush) -> bool`。这些函数不是 Application 的子组件，而是平台特定的工具函数。它们保留 `from .appenv import appenv` 导入作为已知例外——CrossRunner 的注册机制要求模块级函数，无法在运行时注入 appenv。

## Consequences

- HostsSaver 类本身已改为构造注入，仅这些模块级函数保留旧模式（全局单例导入）。
