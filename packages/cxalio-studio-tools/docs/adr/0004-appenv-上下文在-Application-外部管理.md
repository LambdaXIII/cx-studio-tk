# appenv 上下文在 Application 外部管理

appenv 是单例，生命周期独立于 Application；因此决定由工具入口代码在外部进入 appenv 上下文（`with appenv:`），然后在内部进入 Application 上下文，而不是由 Application 管理 appenv 的启动/停止。

## Consequences

- appenv 的启动/停止与 Application 的启动/停止解耦。
- Application 只负责 context 的生命周期管理和工具特定的启动/清理。
