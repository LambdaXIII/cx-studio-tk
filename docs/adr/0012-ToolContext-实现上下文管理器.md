# <Tool>Context 实现上下文管理器

> 领域：cxalio-studio-tools（应用框架）· 适用范围：cxalio-studio-tools 框架与全部工具

`<Tool>Context` 持有运行时资源（如临时目录、MediaDB 连接、FileList），需要确定性清理；因此决定让它实现上下文管理器协议：`__enter__`/`__exit__` + `start()`/`stop()`，与 Application 的生命周期协议一致——Application 在 `__enter__` 中启动 context、在 `__exit__` 中停止 context。`cleanup()` 方法作为 `stop()` 的别名，支持非上下文管理器场景下的手动清理。

## Consequences

- Application 用统一的上下文协议驱动 context 的启动与清理，保证异常路径下资源也被确定性释放。
- context 生命周期由 Application 管理，与 appenv 相互独立。
