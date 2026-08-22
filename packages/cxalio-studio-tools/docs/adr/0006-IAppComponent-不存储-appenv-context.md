# IAppComponent 不存储 appenv/context

旧设计中 `IAppComponent` 通过 `self._context = context` + `@property context(self) -> IAppContext` 提供统一的 appenv/context 访问。但这导致子类的 `self.context` 类型被物化为 `IAppContext`——即使子类的 `__init__` 签名为 `context: <Tool>Context`，Pylance 仍通过基类 property 将类型收窄为接口。因此决定：`IAppComponent.__init__` 仅作为签名契约（参数 optional），不存储、不暴露；子类在各自的 `__init__` 中自行赋值：

```python
class SomeToolComponent(IAppComponent):
    def __init__(self, appenv: IAppEnvironment, context: <Tool>Context, ...):
        super().__init__(appenv, context)
        self.appenv = appenv      # 类型为 IAppEnvironment
        self.context = context    # Pylance 推断为 <Tool>Context
```

这样 `self.context` 的类型从子类的参数声明推断，不再被基类收窄。

## Consequences

- `Application` 子类必须同时存储 `self.appenv` 和 `self.context`；其他 IAppComponent 子类只存储自己需要的（当前项目实践中所有子类最终都需要两者）。
