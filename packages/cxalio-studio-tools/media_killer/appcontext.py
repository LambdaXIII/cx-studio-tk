from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Literal

from cx_tools.app.safe_error import SafeError
from cx_tools.i18n import _


@dataclass
class AppContext:
    """命令行参数上下文。

    封装 mediakiller 所有命令行选项的解析结果。
    唯一入口是 :meth:`from_arguments`，禁止直接构造。
    """

    # 输入路径列表（位置参数）
    inputs: list[str] = field(default_factory=list)

    # 覆盖模式
    force_overwrite: bool = False  # -y
    force_no_overwrite: bool = False  # -n

    # 输出目录
    output_dir: str | None = None  # -o

    # 并发数
    max_workers: int = 1  # -j

    # 假装模式
    pretending_mode: bool = False  # -p

    # 继续模式
    continue_mode: bool = False  # -c

    # 脚本保存
    save_script: str | None = None  # -s

    # 调试模式
    debug_mode: bool = False  # -d

    # 帮助
    show_help: bool = False  # -h
    show_full_help: bool = False  # --tutorial

    # 生成示例预设
    generate: str | None = None  # -g

    # 排序模式
    sort_mode: Literal["source", "preset", "target", "x"] = "source"  # --sort

    @classmethod
    def from_arguments(cls, arguments: list[str]) -> AppContext:
        """从命令行参数解析。

        Args:
            arguments: 命令行参数列表（不含程序名）

        Returns:
            AppContext: 解析后的上下文

        Raises:
            SafeError: 参数互斥冲突时抛出
        """
        parser = cls._make_parser()
        parsed = parser.parse_args(arguments)

        # 互斥检查：-y 与 -n 不可同时指定
        if parsed.force_overwrite and parsed.force_no_overwrite:
            raise SafeError(_("-y（强制覆盖）与 -n（强制不覆盖）不可同时使用。"))

        # 白名单赋值：只取 dataclass 中声明的字段
        context = cls()
        context.inputs = parsed.inputs
        context.force_overwrite = parsed.force_overwrite
        context.force_no_overwrite = parsed.force_no_overwrite
        context.output_dir = parsed.output_dir
        context.max_workers = parsed.max_workers
        context.pretending_mode = parsed.pretending_mode
        context.continue_mode = parsed.continue_mode
        context.save_script = parsed.save_script
        context.debug_mode = parsed.debug_mode
        context.show_help = parsed.show_help
        context.show_full_help = parsed.show_full_help
        context.generate = parsed.generate
        context.sort_mode = parsed.sort_mode

        return context

    @staticmethod
    def _make_parser() -> argparse.ArgumentParser:
        """构建内部参数解析器。

        私有方法，不对外暴露 argparse 细节。
        """
        parser = argparse.ArgumentParser(
            prog="mediakiller",
            add_help=False,
        )

        # 位置参数：输入路径
        parser.add_argument(
            "inputs",
            nargs="*",
            default=[],
        )

        # 覆盖控制
        parser.add_argument(
            "-y",
            "--overwrite",
            action="store_true",
            dest="force_overwrite",
        )
        parser.add_argument(
            "-n",
            "--no-overwrite",
            action="store_true",
            dest="force_no_overwrite",
        )

        # 输出目录
        parser.add_argument(
            "-o",
            "--output",
            dest="output_dir",
        )

        # 并发数
        parser.add_argument(
            "-j",
            "--jobs",
            "--max-workers",
            type=int,
            default=1,
            dest="max_workers",
        )

        # 假装模式
        parser.add_argument(
            "-p",
            "--pretend",
            action="store_true",
            dest="pretending_mode",
        )

        # 继续模式
        parser.add_argument(
            "-c",
            "--continue",
            action="store_true",
            dest="continue_mode",
        )

        # 脚本保存
        parser.add_argument(
            "-s",
            "--save",
            dest="save_script",
        )

        # 调试模式
        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            dest="debug_mode",
        )

        # 帮助
        parser.add_argument(
            "-h",
            "--help",
            action="store_true",
            dest="show_help",
        )
        parser.add_argument(
            "--tutorial",
            "--full-help",
            action="store_true",
            dest="show_full_help",
        )

        # 生成示例预设
        parser.add_argument(
            "-g",
            "--generate",
            dest="generate",
        )

        # 排序模式
        parser.add_argument(
            "--sort",
            default="source",
            choices=["source", "preset", "target", "x"],
            dest="sort_mode",
        )

        return parser
