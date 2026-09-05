# common/components 公共能力在设计之初规划

> 领域：cxalio-studio-tools（应用框架）· 适用范围：cxalio-studio-tools 框架与全部工具

工具内部分层 common/（不需要 appenv 的非耦合能力）与 components/（需要 appenv 或含工具特定转化/包装逻辑）的判别标准是 appenv 依赖 + 特化与否：不依赖 appenv 且非工具特定 → common；否则 → components。决定：公共能力在设计之初规划（非消费者驱动），避免事后从 components 反向抽取。

## Consequences

- 保持 common/ 作为工具间稳定的对外组合面（工具间 import 只允许指向 `package.common`）。
- 避免为满足单个消费者而事后从 components 反向抽取公共能力，维护分层边界的清晰。
