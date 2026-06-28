from cx_tools.i18n import _

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Self, override

from cx_studio.system import system_open
from cx_tools.app import IApplication
from cx_wealth import WealthDetailPanel, IndexedListPanel, WealthLabel
from cx_wealth import rich_types as r
from .app_help import AppHelp
from .appenv import appenv
from .hosts_builder import HostsBuilder
from .hosts_saver import HostsSaver, dns_flush
from .profile_manager import ProfileManager


class Application(IApplication):
    def __init__(self, arguments: Sequence[str] | None = None) -> None:
        super().__init__(arguments or sys.argv[1:])
        self.profile_manager = ProfileManager()

    @override
    def start(self) -> None:
        appenv.load_arguments(self.sys_arguments)
        appenv.start()
        if appenv.is_debug_mode_on():
            appenv.say(f"[cx.warning]{_('调试模式已开启。')}[/]")
            appenv.whisper(
                IndexedListPanel(
                    [WealthLabel(x) for x in self.profile_manager.profiles.values()],
                    title="已找到配置文件",
                )
            )

    @override
    def stop(self) -> None:
        appenv.stop()

    @staticmethod
    def __open_file(file_path: Path) -> None:
        editor = os.environ.get("EDITOR", None)
        if editor:
            subprocess.run(f"{editor} {file_path.absolute()}", shell=True)
            return

        appenv.whisper(f"[cx.warning]未设置编辑器环境变量，尝试使用系统工具打开。")
        result = system_open(file_path)
        if not result:
            url = f"file://{file_path.resolve()}"
            appenv.say(f"[cx.error]打开文件 [link={url}]{file_path.name}[/link] 失败。")

    @staticmethod
    def __open_dir(dir_path: Path) -> None:
        result = system_open(dir_path)
        if not result:
            url = f"file://{dir_path.resolve()}"
            appenv.say(f"[cx.error]打开目录 [link={url}]{dir_path.name}[/link] 失败。")

    def command_new(self) -> None:
        profile_id = appenv.context.profile_id
        assert profile_id is not None, "profile_id 不能为空"
        filename = self.profile_manager.generate_profile_path(profile_id)
        if filename.exists():
            appenv.say(
                f"[cx.error]{_('配置文件 {name} 已存在。').format(name=filename.name)}[/]"
            )
            return

        filename = self.profile_manager.create_profile(profile_id, filename)
        if filename:
            appenv.say(
                f"[cx.success]已创建配置文件: [link=file://{filename.resolve()}]{filename.name}[/link]"
            )
        else:
            appenv.say(f"[cx.error]创建配置文件失败。")
            return

        self.__open_file(filename)

    def command_list(self) -> None:
        table = r.Table(
            r.Column("ID", highlight=False, style="yellow"),
            r.Column("Name", highlight=False, style="cyan"),
            r.Column("Description", highlight=False, style="green"),
            r.Column("Enabled", highlight=False),
            box=r.box.HORIZONTALS,
            border_style="dim blue",
            header_style="bold blue",
        )
        for profile in self.profile_manager.find_profile(appenv.context.search_pattern):
            table.add_row(
                profile.id,
                profile.name,
                profile.description,
                "[cx.success]YES[/]" if profile.enabled else "[cx.error]NO[/]",
            )
        if table.row_count == 0:
            appenv.say(f"[cx.warning]{_('未找到符合条件的配置文件。')}[/]")
        else:
            appenv.say(table)
            appenv.say(f"[cx.success]共找到 {table.row_count} 个配置文件。")
            appenv.say(
                f"[dim]{_('可尝试使用 show 或 edit 命令查看或编辑配置文件。')}[/]"
            )

    def command_show(self) -> None:
        assert appenv.context.profile_id is not None, "profile_id 不能为空"
        profile = self.profile_manager.profiles.get(appenv.context.profile_id, None)
        if profile:
            appenv.say(WealthDetailPanel(profile, title=profile.id))  # type: ignore[arg-type]  # Profile 为 dataclass，运行时兼容 WealthDetailMixin
        else:
            appenv.say(
                f"[cx.error]未找到 ID 为 {appenv.context.profile_id} 的配置文件。"
            )

    def command_edit(self) -> None:
        profile_id = appenv.context.profile_id
        assert profile_id is not None, "profile_id 不能为空"
        profile = self.profile_manager.profiles.get(profile_id, None)

        if profile is None:
            appenv.say(f"[cx.error]未找到 ID 为 {profile_id} 的配置文件。")
            return

        file_path = profile.path.resolve()
        if not file_path.exists():
            appenv.say(f"[cx.error]配置文件 [filepath]{file_path}[/filepath] 不存在。")
            return

        if file_path.is_dir():
            self.__open_dir(file_path)
        else:
            self.__open_file(file_path)

    def command_update(self) -> None:
        appenv.whisper("update 模式已启动")
        builder = HostsBuilder()
        appenv.whisper("已构建 HostBuilder")

        enabled_profiles = list(self.profile_manager.enabled_profiles)
        appenv.whisper(
            IndexedListPanel(
                [WealthLabel(x) for x in enabled_profiles], title="已启用配置文件"
            )
        )

        appenv.whisper("开始构建 Hosts 文件内容")
        lines = builder.iter_lines(enabled_profiles)

        # 保存临时文件；使用不带 BOM 的 utf-8 写入，因为系统 DNS 解析器不期望 BOM
        with appenv.temp_hosts.open("w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        appenv.whisper(
            _("已写入新的内容到临时文件 {path}").format(path=appenv.temp_hosts)
        )

        saver = HostsSaver()
        save_target = None
        if appenv.context.save_target:
            save_target = Path(appenv.context.save_target)
            appenv.whisper(f"将保存到目标文件 {save_target}")
        saved = saver.save(save_target)
        if saved:
            appenv.say(f"[cx.success]{_('已成功保存新的 hosts 文件。')}[/]")
            if save_target is None:  # 仅系统 hosts 路径才需刷新 DNS 缓存
                appenv.whisper(
                    f"准备刷新 DNS 缓存（skip_flush={appenv.context.skip_flush}）"
                )
                try:
                    dns_flush(skip_flush=appenv.context.skip_flush)
                except NotImplementedError:
                    appenv.say(
                        "[cx.info]hosts 文件已更新。当前平台不支持自动刷新 DNS 缓存。"
                    )

    def command_help(self) -> None:
        AppHelp.show_help(appenv.console)

    def run(self) -> None:
        if appenv.context.command == "help" or appenv.context.show_help:
            self.command_help()
            return

        if appenv.context.show_full_help:
            AppHelp.show_full_help(appenv.console)
            return

        if appenv.context.command == "new":
            self.command_new()
            return

        if appenv.context.command == "list":
            self.command_list()
            return

        if appenv.context.command == "show":
            self.command_show()
            return

        if appenv.context.command == "edit":
            self.command_edit()
            return

        if appenv.context.command == "update":
            self.command_update()
            return

        self.command_help()
