# Tasks

## 1. 主题字段样式值

- [x] 1.1 `appenv.py` 的 `CX_NOTE_STYLES`：`cx.note.dropped` 改为红色加删除线加变暗，`cx.note.done` 改为绿色加变暗
- [x] 1.2 `list_view.py` 的 `make_entry_block` docstring 与行内注释同步两字段的样式语义描述（red+strike+dim、green+dim）

## 2. 版本迭代

- [x] 2.1 版本号 1.4.1（用户已拍板）：以 pyproject 旧值 `1.4.0` 为起点写入变更包 `cx_note/__init__.py` 的 `__version__ = "1.4.1"`，`pyproject.toml` 随之同步为 `1.4.1`

## 3. 验证

- [x] 3.1 实机冒烟：构造含待办/进行中/已完成/已取消/超龄条目的库，逐一验证 `list`、`drop` 回显、`erase` 回显、`clear` 回显与收尾清理报告——消亡条目红色+删除线+变暗、非消亡已完成绿色+变暗、待办/进行中无样式，`--json` 无装饰
- [x] 3.2 `uv run black .` 格式化；`openspec validate add-dim-status-styles --strict` 通过

## Workflow follow-up

- 实施完成后 sync 主规格 → archive → merge 回 dev
