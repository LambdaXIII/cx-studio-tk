# Progress 不入通用接口

say/whisper 只需要 console，不需要知道具体的 Live 组件类型；工具可能使用任意 Live 组件（Progress、Status、自定义 Live 等），不仅仅是 Progress。通用接口不应假设具体类型——这样设计可以在特化融合的同时保证兼容性。因此决定：IAppEnvironment 不持有 Progress 引用，IApplication 不接受 Progress 参数。

## Considered Options

- **IAppEnvironment 持有 Progress 引用（已否决）**：IAppEnvironment 提供 say/whisper 输出能力，内部只需要 console，不应知道 Progress 或其他具体 Live 组件的存在；持有 Progress 引用等于假设所有工具都使用 Progress，破坏通用性。
- **IApplication 接受 Progress 参数（已否决）**：Progress 是工具特定的 UI 组件，不是所有工具都需要（media_scout、jpegger 不需要），也不是所有工具都用 Progress（可能用其他 Live 组件）。

## Consequences

- Progress 完全属于工具内部：具体 `<Tool>Env` 子类创建 progress（`console=self.console`），Rich Live 接管该 console 的输出，`self.console.print()` 在 Live 运行期间自动暂停渲染、输出文本、恢复渲染，无需手动 stop/start。
- `<Tool>Env` 子类不应 override `say()`/`whisper()` 来协调 progress；具体 Application 子类可接受 progress 参数（从 `appenv.progress` 获取）。
- 第三方复用 Application 时提供自己的 appenv（如果有 progress 则在 appenv 中提供），Application 从 appenv 获取。不同工具可以使用不同的 Live 组件，say/whisper 的协调逻辑在各自的 `<Tool>Env` 子类中实现，互不干扰。
