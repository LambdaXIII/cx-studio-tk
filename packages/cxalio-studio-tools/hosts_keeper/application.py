from hosts_keeper.i18n import _

import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Self, override

from cx_studio.system import system_open
from cx_tools.app import IApplication, IAppEnvironment
from cx_wealthy import WealthyDetailPanel, IndexedListPanel, RichLabel
from cx_wealthy import rich_types as r
from .app_help import HostsKeeperHelp
from .appcontext import AppContext
from .hosts_builder import HostsBuilder
from .hosts_saver import HostsSaver, dns_flush
from .profile_manager import ProfileManager


class HostsKeeperApp(IApplication):

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: AppContext,
        progress: r.Progress | None = None,
    ) -> None:
        super().__init__(appenv, context)
        self.context = context
        self.progress = progress
        self.profile_manager = ProfileManager(context=self.context, appenv=self.appenv)

    @override
    def start(self) -> None:
        self.appenv.set_debug_mode(self.context.debug_mode)
        if self.context.debug_mode:
            self.appenv.say(f"[cx.warning]{_('调试模式已开启。')}[/]")
            self.appenv.whisper(
                IndexedListPanel(
                    [RichLabel(x) for x in self.profile_manager.profiles.values()],
                    title=_("已找到配置文件"),
                )
            )

    @override
    def stop(self) -> None:
        pass

    @override
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        result = super().__exit__(exc_type, exc_val, exc_tb)
        if exc_type is KeyboardInterrupt:
            self.appenv.say(f"[cx.error]{_('用户中断')}[/]")
            result = True
        return result

    def __open_file(self, file_path: Path) -> None:
        editor = os.environ.get("EDITOR", None)
        if editor:
            subprocess.run(f"{editor} {file_path.absolute()}", shell=True)
            return

        self.appenv.whisper(
            f"[cx.warning]{_('未设置编辑器环境变量，尝试使用系统工具打开。')}"
        )
        result = system_open(file_path)
        if not result:
            self.appenv.say(
                f"[cx.error]{_('打开文件 {name} 失败。').format(name=file_path.name)}[/]"
            )

    def __open_dir(self, dir_path: Path) -> None:
        result = system_open(dir_path)
        if not result:
            self.appenv.say(
                f"[cx.error]{_('打开目录 {name} 失败。').format(name=dir_path.name)}[/]"
            )

    def command_new(self) -> None:
        profile_id = self.context.profile_id
        assert profile_id is not None, _("profile_id 不能为空")
        filename = self.profile_manager.generate_profile_path(profile_id)
        if filename.exists():
            self.appenv.say(
                f"[cx.error]{_('配置文件 {name} 已存在。').format(name=filename.name)}[/]"
            )
            return

        filename = self.profile_manager.create_profile(profile_id, filename)
        if filename:
            self.appenv.say(
                f"[cx.success]{_('已创建配置文件: {name}').format(name=filename.name)}[/]"
            )
        else:
            self.appenv.say(f"[cx.error]{_('创建配置文件失败。')}[/]")
            return

        self.__open_file(filename)

    def command_list(self) -> None:
        table = r.Table(
            r.Column(_("ID"), highlight=False, style="yellow"),
            r.Column(_("Name"), highlight=False, style="cyan"),
            r.Column(_("Description"), highlight=False, style="green"),
            r.Column(_("Enabled"), highlight=False),
            box=r.box.HORIZONTALS,
            border_style="dim blue",
            header_style="bold blue",
        )
        for profile in self.profile_manager.find_profile(self.context.search_pattern):
            table.add_row(
                profile.id,
                profile.name,
                profile.description,
                "[cx.success]YES[/]" if profile.enabled else "[cx.error]NO[/]",
            )
        if table.row_count == 0:
            self.appenv.say(f"[cx.warning]{_('未找到符合条件的配置文件。')}[/]")
        else:
            self.appenv.say(table)
            self.appenv.say(
                f"[cx.success]{_('共找到 {count} 个配置文件。').format(count=table.row_count)}[/]"
            )
            self.appenv.say(
                f"[dim]{_('可尝试使用 show 或 edit 命令查看或编辑配置文件。')}[/]"
            )

    def command_show(self) -> None:
        assert self.context.profile_id is not None, _("profile_id 不能为空")
        profile = self.profile_manager.profiles.get(self.context.profile_id, None)
        if profile:
            self.appenv.say(WealthyDetailPanel(profile, title=profile.id))  # type: ignore[arg-type]  # Profile 为 dataclass，运行时兼容 WealthDetailMixin
        else:
            self.appenv.say(
                f"[cx.error]{_('未找到 ID 为 {profile_id} 的配置文件。').format(profile_id=self.context.profile_id)}[/]"
            )

    def command_edit(self) -> None:
        profile_id = self.context.profile_id
        assert profile_id is not None, _("profile_id 不能为空")
        profile = self.profile_manager.profiles.get(profile_id, None)

        if profile is None:
            self.appenv.say(
                f"[cx.error]{_('未找到 ID 为 {profile_id} 的配置文件。').format(profile_id=profile_id)}[/]"
            )
            return

        file_path = profile.path.resolve()
        if not file_path.exists():
            self.appenv.say(
                f"[cx.error]{_('配置文件 {path} 不存在。').format(path=str(file_path))}[/]"
            )
            return

        if file_path.is_dir():
            self.__open_dir(file_path)
        else:
            self.__open_file(file_path)

    def command_update(self) -> None:
        self.appenv.whisper(_("update 模式已启动"))
        assert self.progress is not None
        builder = HostsBuilder(
            context=self.context, appenv=self.appenv, progress=self.progress
        )
        self.appenv.whisper(_("已构建 HostBuilder"))

        enabled_profiles = list(self.profile_manager.enabled_profiles)
        self.appenv.whisper(
            IndexedListPanel(
                [RichLabel(x) for x in enabled_profiles], title=_("已启用配置文件")
            )
        )

        self.appenv.whisper(_("开始构建 Hosts 文件内容"))
        lines = builder.iter_lines(enabled_profiles)
        # 先将 generator 耗尽让 async 完成，再停 progress
        with self.context.temp_hosts.open("w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        if self.progress is not None:
            self.progress.stop()
        self.appenv.whisper(
            _("已写入新的内容到临时文件 {path}").format(path=self.context.temp_hosts)
        )

        saver = HostsSaver(context=self.context, appenv=self.appenv)
        save_target = None
        if self.context.save_target:
            save_target = Path(self.context.save_target)
            self.appenv.whisper(
                f"{_('将保存到目标文件 {path}').format(path=save_target)}"
            )
        saved = saver.save(save_target)
        if saved:
            self.appenv.say(f"[cx.success]{_('已成功保存新的 hosts 文件。')}[/]")
            if save_target is None:  # 仅系统 hosts 路径才需刷新 DNS 缓存
                self.appenv.whisper(
                    f"{_('准备刷新 DNS 缓存')}（skip_flush={self.context.skip_flush}）"
                )
                try:
                    dns_flush(skip_flush=self.context.skip_flush)
                except NotImplementedError:
                    self.appenv.say(
                        f"[cx.info]{_('hosts 文件已更新。当前平台不支持自动刷新 DNS 缓存。')}"
                    )

    def command_help(self) -> None:
        help_component = HostsKeeperHelp(self.appenv, self.context)
        help_component.show_help()

    def run(self) -> None:
        if self.context.command == "help" or self.context.show_help:
            self.command_help()
            return

        if self.context.show_full_help:
            help_component = HostsKeeperHelp(self.appenv, self.context)
            help_component.show_full_help()
            return

        if self.context.command == "new":
            self.command_new()
            return

        if self.context.command == "list":
            self.command_list()
            return

        if self.context.command == "show":
            self.command_show()
            return

        if self.context.command == "edit":
            self.command_edit()
            return

        if self.context.command == "update":
            self.command_update()
            return

        self.command_help()
