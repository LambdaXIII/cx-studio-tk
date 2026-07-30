"""media_killer 命令行上下文。

持有命令行参数解析结果和运行时状态。
"""

from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, override

from cx_studio.filesystem import FileList
from cx_tools.app import ConfigManager, IAppContext, SafeError
from media_killer.i18n import _

from .media import MediaDB

# 覆盖模式三态
OVERWRITE_DANGER = "danger"  # -y 指定，强制覆盖
OVERWRITE_SAFE = "safe"  # -n 指定，安全模式


@dataclass
class AppContext(IAppContext):
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

    def __post_init__(self) -> None:
        """dataclass 后处理：初始化 IAppContext 基类和运行时资源。"""
        super().__init__()

        # 配置管理器
        self._config_manager = ConfigManager("MediaKiller")

        # MediaDB 实例（延迟 connect）
        db_path = self._config_manager.get_file("media_info.db")
        self._media_db = MediaDB(db_path=db_path)

        # 文件列表（FileList 自动去重 + 延迟大小计算）
        sizer = self._media_db.make_file_bytes_getter()
        self._garbage_files = FileList(sizer_function=sizer)
        self._processed_files = FileList(sizer_function=sizer)
        self._generated_files = FileList(sizer_function=sizer)

    @property
    def overwrite_mode(self) -> str | None:
        """将 ``-y``/``-n`` 解析为三态值。

        Returns:
            ``OVERWRITE_DANGER``: ``-y`` 已指定，强制覆盖
            ``OVERWRITE_SAFE``: ``-n`` 已指定，安全模式
            ``None``: 两者均未指定
        """
        if self.force_no_overwrite:
            return OVERWRITE_SAFE
        if self.force_overwrite:
            return OVERWRITE_DANGER
        return None

    @property
    def config_manager(self) -> ConfigManager:
        """配置管理器。"""
        return self._config_manager

    @property
    def media_db(self) -> MediaDB:
        """MediaDB 实例。"""
        return self._media_db

    @property
    def garbage_files(self) -> FileList:
        """待清理的垃圾文件列表。"""
        return self._garbage_files

    @property
    def processed_files(self) -> FileList:
        """已处理的文件列表。"""
        return self._processed_files

    @property
    def generated_files(self) -> FileList:
        """已生成的文件列表。"""
        return self._generated_files

    @override
    def start(self) -> None:
        """启动上下文：连接 MediaDB。"""
        super().start()
        self._media_db.connect()

    @override
    def stop(self) -> None:
        """停止上下文：清理资源。

        先关闭 MediaDB、清理旧日志、清理临时目录，
        再调用 super().stop()。
        注意：context 不持有 appenv，因此不在此输出任何内容。
        """
        self._media_db.close()
        self._config_manager.remove_old_log_files()
        super().stop()

    def cleanup(self) -> None:
        """退出阶段统一扫尾清理（仅文件清理，无输出）。

        删除 garbage_files 中的垃圾文件，不输出任何报告。
        报告输出由 Application 负责。
        """
        if len(self._garbage_files) > 0:
            for filename in self._garbage_files:
                self._unlink_with_retry(filename)
            self._garbage_files.clear()

    def add_garbage_files(self, *filenames: str | Path) -> None:
        """添加 garbage 文件。

        Args:
            filenames: 文件路径列表
        """
        for f in filenames:
            self._garbage_files.append(Path(f))

    @staticmethod
    def _unlink_with_retry(
        filename: Path, max_retries: int = 3, delay: float = 0.5
    ) -> None:
        """删除文件，遇 PermissionError 重试。

        静默失败——不输出任何内容（context 不持有 appenv）。

        Args:
            filename: 要删除的文件路径
            max_retries: 最大重试次数
            delay: 重试间隔（秒）
        """
        for attempt in range(max_retries):
            try:
                filename.unlink(missing_ok=True)
                return
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                # 最后一次重试失败：静默跳过
            except OSError:
                # 其他文件系统错误也跳过，不阻塞清理流程
                break

    def pretending_sleep(self, interval: float = 0.2) -> None:
        """模拟运行模式下的同步睡眠。

        若处于假装模式，睡眠指定时间。

        Args:
            interval: 睡眠秒数
        """
        if self.pretending_mode:
            time.sleep(interval)

    async def pretending_asleep(self, interval: float = 0.2) -> None:
        """模拟运行模式下的异步睡眠。

        若处于假装模式，异步睡眠指定时间。

        Args:
            interval: 睡眠秒数
        """
        if self.pretending_mode:
            await asyncio.sleep(interval)

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
