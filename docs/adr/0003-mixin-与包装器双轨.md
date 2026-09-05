# 渲染协议用 mixin + 包装器双轨承载

> 领域：cx-wealthy · 适用范围：cx-wealthy

渲染协议用 mixin 承载（非 Protocol）：mixin 提供默认 `__rich__` 实现，使 `console.print(obj)` 直接输出正确渲染——"协议即渲染"。同时提供包装器（`RichLabel`/`WealthyDetailPanel`）给不愿或不能继承的使用方（第三方类型、frozen dataclass 继承位已满等），两者共享底层渲染逻辑。

## Considered Options

- **Protocol-only（不提供 mixin 默认实现）**：Protocol 不允许带方法体，"协议即渲染"无法成立——所有使用方都必须显式 `console.print(RichLabel(obj))`，丢失直接打印的体验。mixin 只定义方法不定义字段，与 frozen dataclass 完全兼容，无实质冲突。
- **Wrapper-only（不提供 mixin，只用包装器）**：detail 面板的 value 若是可展示对象，需要该对象**自身具备 `__rich__`** 才能自动以标签形态嵌套渲染。包装器 `RichLabel(obj)` 是外层包装，`obj` 自身没有 `__rich__`，在 detail 面板中作为 value 时不会被识别为可渲染对象。mixin 让对象自身具备 `__rich__`，是 detail 嵌套渲染的前置依赖。
- **复用 `__rich_repr__` 替代 `__rich_detail__`**：repr 的 value 由 `Pretty` 渲染（repr 风格），没有"value 若实现同协议则自动嵌套为 sub-panel"的约定，丢失嵌套展示能力。展示场景使用方需要预格式化（如 `str(path)` → 文件名而非 `PosixPath('/foo/bar')`），repr 期望 raw 值，复用会强制使用方在 yield 前自行包装，更繁琐。

## Consequences

- 使用方二选一：继承 mixin（协议即渲染）或显式包装（不继承）；两种路径渲染结果一致。
- detail 面板的嵌套渲染依赖对象自身具备 `__rich__`（经 mixin 或手工实现）。
