# Tasks

> 背景：media_killer 输入侧重构为「输入解析 → `[Path]` → 资源提炼与任务组装」两环节，修复目录输入被误判为预设的 bug。设计与行为契约见同目录 proposal.md / design.md / specs/media-killer/spec.md。全部改动集中于 `packages/cxalio-studio-tools/media_killer/`，单会话顺序执行即可，无需委派。

## 1. 环节一：输入解析组件

- [x] 1.1 新建 `components/input_resolver.py`：`InputResolver.resolve(*inputs: str) -> list[Path]`——每条输入基于 CWD 解析为绝对路径；不存在且无扩展名时追加 `.toml` 判定（命中须为文件），仍不存在抛 `SafeError`（消息含该输入），带扩展名的缺失输入直接报错不补全；原始输入 `os.access` 检测不过抛 `SafeError`（消息含路径）；目录递归展开（rglob 全量，不按源后缀过滤）；项目文件交自持的 InspectorChain（六个 Inspector 组装自 application 移入；项目文件扩展名集合随 expander 移入并扩充 `.ps1`/`.sh`；链在每次 `resolve()` 内以 `with` 使用、关闭其内部去重，查重统一在集合层按绝对路径执行），项目文件内相对路径基于项目文件位置解析，引用只做存在性过滤（缺失静默跳过，后缀筛选归环节二），解析异常包装为 `SafeError`；结果按绝对路径查重并排序（大小写折叠随平台语义）；公开符号补 docstring（Google 风格、简体中文）
- [x] 1.2 删除 `components/expander.py`，更新 `components/__init__.py` 的导出面与模块 docstring（`SourceExpander` 除名、`InputResolver` 入列）

## 2. 环节二：编排重排与 i18n

- [x] 2.1 重排 `application.py` 的 `run()` 步骤 4-6（design D3/D4）：改为「`InputResolver().resolve(*ctx.inputs)` → 提炼（抽为模块级纯函数 `_extract_presets_and_sources(paths)`：`.toml` 交 `PresetLoader`，失败经 `SafeError` 包装沿用现模板；预设详情面板与「配置文件路径」whisper 保留）→ 合并 `source_suffixes` 过滤其余路径为源 → 任务组装」；删除 `_resolve_preset` 与源存在性事后检查、删除逐条「媒体来源路径」whisper；汇总句改为「已添加 N 个配置文件和 M 个源文件」（口径 = 过滤后源文件数）
- [x] 2.2 i18n：环节一新增的用户可见文案（不存在/不可读报错）登记 msgid，按 `docs/agents/i18n.md` 跑 pybabel 提取/更新/编译（media-killer domain），并清理不再引用的 msgid（「源文件不存在」）
- [x] 2.3 同步引用旧符号的文档：`CONTEXT.md` 组件清单与两环节表述、`ffpretty/common/mission.py` 模块 docstring 的 `SourceExpander` 引用；`app_help.py` 中 `--sort x`「按输入顺序」的描述

## 3. 验证（阶段检查点）

- [x] 3.1 冒烟脚本放 `temp/` 下（临时产物不入包），前置备份并在结束后恢复 `~/.config/cx-studio/MediaKiller/last_missions.xml`，`-c` 用例置于全部报错用例之前；主用例：复刻原 bug 场景——预设 toml + 无扩展名目录（内含媒体文件与一个有效 toml）+ `--pretend`，验证不再报 PermissionError、任务数断言按「提取的预设数 × 源数」；变更面边界用例：不存在的输入报错指明路径、带扩展名缺失输入不补全、无扩展名输入补全 `.toml`、目录内无效 toml 报错中止、缺少必需节的 toml 报错中止、同文件双输入只保留一份、`--continue` 叠加去重
- [x] 3.2 `uv run black .`
- [x] 3.3 `openspec validate "fix-mediakiller-input-resolution" --strict`——INFO 级提示当错误处理

## 4. 收口

- [x] 4.1 向用户建议版本号（读 `packages/cxalio-studio-tools/pyproject.toml` 旧值；初步判断 minor 档——新增能力面：目录内 toml 成为预设、项目文件门扩充，AGENTS 幅度策略多档取最高；最终由用户拍板）
- [x] 4.2 实施经用户确认后 `openspec archive` 归档本变更（delta 折回 `openspec/specs/media-killer/spec.md`）
