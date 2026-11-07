# Proposal

## Why

mediakiller 对无扩展名的目录输入报「加载预设文件 {path} 失败: [Errno 13] Permission denied」：`_resolve_preset`（application.py）把存在的无扩展名路径一律判为预设候选，目录在这一步被吸进预设侧，永远到不了 `SourceExpander` 的目录展开——而「目录递归展开」正是 help 文档承诺的输入行为。根因是现行输入处理采用「逐条分类」模型（每条输入先二选一为预设或源），且源展开的后缀过滤依赖已加载预设，形成倒挂依赖；按「先解析后提取」重构为两个解耦环节后，此 bug 自然消失，且两环节各自可独立验证。

## What Changes

- 输入处理重构为两个互不依赖的环节，衔接仅为 `[Path]`：
  - **输入解析**：原始输入字符串集合 → 存在、可读、绝对的路径集合（逐条解析路径、目录递归展开、项目文件经 InspectorChain 解析、查重、排序）；本环节不感知预设与源后缀，仅有的格式感知是缺失输入的 `.toml` 补全与项目文件类型识别（项目文件扩展名门按裁定扩充 `.ps1`/`.sh`，与 Inspector 面对齐）。
  - **资源提炼与任务组装**：从路径集合中提取有效 `.toml` 为预设（加载失败报错中止），其余路径按合并的 `source_suffixes` 过滤为源，组装 missions；mission 级排序去重与 `--continue` 叠加保持不变。
- 修复：目录输入不再被误判为预设文件，一律进入展开（本变更的触发 bug）。
- 后缀过滤从展开阶段移至预设提取之后——展开成为纯结构动作，消除对预设的倒挂依赖。
- 删除 `_resolve_preset` 的逐条分类；无扩展名补全 `.toml` 保留，但仅在路径不存在时生效（存在的目录永远先被展开）。
- 新建能力域规格 `media-killer`（此前无 spec），承载输入解析与资源提炼的行为契约。

## Capabilities

### New Capabilities

- `media-killer`: media_killer CLI 的输入解析（原始字符串 → 路径集合）与资源提炼（路径集合 → 预设与源 → missions）行为契约，含各环节的报错形态。

### Modified Capabilities

（无——media-killer 为新建能力域，不存在待修改的现行需求。）

## Impact

- **代码**：`packages/cxalio-studio-tools/media_killer/`——`application.py`（输入处理步骤重排、提炼抽为纯函数、删除 `_resolve_preset`）、`components/input_resolver.py`（新建，取代后删除的 `components/expander.py`）；`components/preset/loader.py` 契约不变，仍由环节二调用。另需同步引用旧符号的文档：`CONTEXT.md` 组件清单、`components/__init__.py` 与 `ffpretty/common/mission.py` 的模块 docstring。
- **行为**：目录输入可用；目录内的 `.toml` 文件会被提取为预设（提取发生在展开之后的自然结果）；无扩展名输入的 `.toml` 补全收窄为仅路径不存在时生效，存在的无扩展名文件改由既有后缀过滤体系排除；`--sort x`「保持输入顺序」随之变为「保持路径集合顺序」；不存在路径的报错文案在输入解析环节统一（原预设侧「预设文件不存在」文案退出该流程，`PresetLoader` 自身契约不变）。
- **i18n**：新增/变更用户可见文案需按 `docs/agents/i18n.md` 走提取与编译流程，并清理不再引用的 msgid。
- **版本**：实施完成后按仓库迭代流程向用户建议版本号（由用户拍板）。
