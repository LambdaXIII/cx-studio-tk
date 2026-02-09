from argparse import ArgumentParser
from collections.abc import Sequence


class AppContext:
    def __init__(self, **kwargs):
        self.command: str | None = None

        self.max_workers: int = 4
        self.profile_id: str | None = None
        self.search_pattern: str | None = None

        self.show_full_help: bool = False
        self.show_help = False

        self.debug_mode: bool = False
        self.pretending_mode: bool = False

        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __rich_repr__(self):
        yield from self.__dict__.items()

    @classmethod
    def from_arguments(cls, args: Sequence[str]) -> "AppContext":
        global_parser = cls.__global_parser()
        main_parser = cls.__command_parser()

        global_args, remaining_args = global_parser.parse_known_args(args)

        cmd_args = main_parser.parse_args(remaining_args)

        for key, value in vars(global_args).items():
            setattr(cmd_args, key, value)

        return cls(**vars(cmd_args))

    @staticmethod
    def __global_parser() -> ArgumentParser:
        parser = ArgumentParser(add_help=False)
        parser.add_argument(
            "-h", "--help", action="store_true", dest="show_help", help="显示此帮助信息"
        )
        parser.add_argument(
            "--tutorial",
            "--full-help",
            action="store_true",
            dest="show_full_help",
            help="显示详细教程",
        )
        parser.add_argument(
            "--debug", "-d", action="store_true", dest="debug_mode", help="开启调试模式"
        )
        parser.add_argument(
            "--pretend",
            "-p",
            action="store_true",
            dest="pretending_mode",
            help="假装执行，不实际更新 hosts 文件",
        )
        return parser

    @staticmethod
    def __command_parser() -> ArgumentParser:
        main_parser = ArgumentParser(add_help=False)
        subparsers = main_parser.add_subparsers(
            dest="command", required=False, help="子命令"
        )

        update_parser = subparsers.add_parser(
            "update", help="更新 hosts 文件", description="更新 hosts 文件"
        )

        list_parser = subparsers.add_parser(
            "list", help="列出所有配置文件", description="列出所有配置文件"
        )
        list_parser.add_argument(
            "--search",
            "-s",
            help="搜索模式",
            dest="search_pattern",
            required=False,
            type=str,
            default="",
        )

        show_parser = subparsers.add_parser(
            "show", help="显示指定配置文件内容", description="显示指定配置文件内容"
        )
        show_parser.add_argument(
            "profile_id", help="配置文件 ID", type=str, metavar="配置文件 ID"
        )

        new_parser = subparsers.add_parser(
            "new", help="创建新配置文件", description="创建新配置文件"
        )
        new_parser.add_argument(
            "profile_id", help="配置文件 ID", type=str, metavar="配置文件 ID"
        )

        edit_parser = subparsers.add_parser(
            "edit", help="编辑指定配置文件", description="编辑指定配置文件"
        )
        edit_parser.add_argument(
            "profile_id", help="配置文件 ID", type=str, metavar="配置文件 ID"
        )

        return main_parser
