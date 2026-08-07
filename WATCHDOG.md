# cx-studio-tk Watchdog

从根目录 `AGENTS.md` 提炼的关键要点，供长时间会话中持续盯防；完整依据以 AGENTS.md 为准。

## 架构边界

- 依赖方向不可反向：`cx-studio` ← `cx-wealthy` ← `cxalio-studio-tools`；cx-wealthy 仅依赖 rich
- 旧包零容忍：出现 `cx_wealth`、`WealthHelp`、`WealthLabel` 或对 `archived/` 的引用——表现为 cx-wealth 不曾存在

## 易被忽略的硬约束

- i18n：工具模块只从自身工具 i18n 导入，不交叉导入；cx-wealthy 不做 i18n
- `# type: ignore` 仅限 Box→Dataclass 桥接边界
- 事件名用 `-ED` 完成式常量（`STARTED`/`FINISHED`），禁止字符串字面量调 `emit()`/`on()`
- Rich 类型必须经 `cx_wealthy.rich_types`，禁止 `import rich.table` 等原生路径
- `__version__` 与 pyproject.toml `version` 保持同步

## 卫生

- 临时/测试/调研产物一律放入 `temp/`（gitignored），不散落项目根或 packages/
- 修改已有文档前先备份当前版本为 `.bak`（不入 git）
