# Tasks

## 1. 主题样式收敛

- [x] 1.1 `cx_note/appenv.py`：`CX_NOTE_STYLES` 中 `cx.note.dropped` 定义改为 `red strike`；删除 `cx.note.expiring` 字段定义

## 2. 条目块渲染统一消亡判定

- [x] 2.1 `cx_note/components/list_view.py`：`make_entry_block` 增加 `taken: bool = False` 形参；「消亡」判定收敛为 `status is DROPPED or expiring or taken`，命中时标号、内容（含多行 Markdown 整体）、提示词「即将被清理」统一挂 `cx.note.dropped`
- [x] 2.2 `cx_note/components/list_view.py`：`build_list_renderable` 增加 `taken: bool = False` 形参并透传给 `make_entry_block`；同步更新两处 docstring 与模块注释中过时的样式描述（dim/strike、yellow 提示词）

## 3. 调用点透传 taken

- [x] 3.1 `cx_note/application.py`：`_echo_changed` 增加 `taken: bool = False` 形参并透传；`_do_erase` 与 `_do_clear` 的回显调用传 `taken=True`（transition/edit/add 回显保持默认）
- [x] 3.2 `cx_note/application.py`：`_finalize` 清理报告的 `build_list_renderable` 调用传 `taken=True`；检查并更新受影响方法的 docstring

## 4. 验证

- [x] 4.1 实机冒烟：构造含待办/进行中/已完成/已取消/超龄终态条目的库，逐一验证 `list`、`drop` 回显、`erase` 回显、`clear` 回显、收尾清理报告的红色+删除线呈现与不变面（非超龄 done 仍 dim、域标题不变、`--json` 无装饰）
- [x] 4.2 `uv run black .` 格式化；确认 `cx.note.expiring` 全仓无残留引用
