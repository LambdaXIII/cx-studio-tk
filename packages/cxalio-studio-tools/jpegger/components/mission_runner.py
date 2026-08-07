"""Jpegger 任务执行器。

`MissionRunner` 负责在指定并发度下执行多个 `Mission`。它在多线程中
调用 PIL 的打开/处理/保存操作，并通过 `IAppEnvironment` 向用户
汇报进度与结果。
"""

from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from threading import Lock

from PIL import Image

from cx_tools.app import IAppComponent, IAppEnvironment, SafeError
from jpegger.i18n import _
from jpegger.appcontext import JpeggerContext
from cx_wealthy import RichLabel
from cx_wealthy import rich_types as r

from .errors import NoSourceFileError, TargetingSourceFileError
from .mission import Mission


class MissionRunner(IAppComponent):
    """并发执行 `Mission` 列表的任务运行器。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文。
        missions: 待执行的任务集合。
        max_workers: 最大并发工作线程数。
    """

    def __init__(
        self,
        appenv: IAppEnvironment,
        context: JpeggerContext,
        missions: list[Mission],
        max_workers: int = 10,
    ):
        super().__init__(appenv, context)
        self.appenv = appenv
        self.context = context
        self.missions = list(missions)
        self.max_workers = max_workers
        # 用于多线程间保护目标目录创建的双检锁。
        self.dir_lock = Lock()

    def check_parent(self, target: Path) -> None:
        """确保目标文件的父目录存在。

        当多线程同时写入同一父目录时，使用锁避免重复创建。

        Args:
            target: 目标文件路径。
        """
        parent = target.parent
        if parent.exists():
            return
        with self.dir_lock:
            # 双检：拿到锁后再次检查，避免其他线程已创建。
            if parent.exists():
                return
            self.appenv.say(f"[yellow]{_('创建目录')} {parent}[/]")
            parent.mkdir(parents=True, exist_ok=True)

    def run_mission(self, mission: Mission) -> None:
        """执行单个任务，并输出结果标签。

        所有已知异常都在本方法内捕获并转化为结果标签，不会向上传播。

        Args:
            mission: 要执行的任务。
        """
        result_tag = "[green]DONE[/]"
        try:
            # 生命周期保证：_context 在构造时已注入，此处断言帮助
            # 类型检查器确认 _context 不是 None。
            assert self.context is not None

            # 1. 校验源文件存在性。
            if not mission.source.exists():
                raise NoSourceFileError(
                    _("源文件 {path} 不存在").format(path=mission.source)
                )

            # 2. 确认目标路径，必要时跳过。
            target = mission.target
            if target.exists():
                if target == mission.source:
                    raise TargetingSourceFileError(
                        _("目标文件 {path} 与源文件相同").format(path=target)
                    )
                if not self.context.overwrite:
                    raise SafeError(
                        _("目标文件 {name} 已存在，跳过。").format(name=target.name),
                        style="yellow",
                    )

            # 3. 确保目标目录存在。
            self.check_parent(target)

            # 4. 打开、过滤、保存。
            # Jpegger 按单张图片处理：Image.open 只读取第一帧，
            # 过滤器链也只作用于该帧。这是符合本工具定位的预期行为。
            img = Image.open(mission.source, **mission.load_options)
            img = mission.filter_chain.run(img)
            img.save(target, format=mission.target_format, **mission.saving_options)
        except Image.UnidentifiedImageError:
            self.appenv.say(
                f"[red]{_('文件 {path} 无法识别，任务跳过！').format(path=mission.source)}[/]"
            )
            result_tag = "[red]ERROR[/]"
        except SafeError as e:
            self.appenv.say(e.message, style=e.style)
            result_tag = "[yellow]SKIPPED[/]"
        except Exception as e:
            self.appenv.say(
                f"[red]{_('文件 {path} 处理失败！').format(path=mission.source)}[/]"
            )
            self.appenv.say(e)
            result_tag = "[red]UNKNOWN ERROR[/]"
        finally:
            self.appenv.say(r.Columns([RichLabel(mission), result_tag], expand=True))

    def run(self) -> None:
        """启动线程池并等待所有任务完成。"""
        with self.appenv.console.status(_("正在执行任务...")) as status:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                pending: set[Future[None]] = {
                    executor.submit(self.run_mission, m) for m in self.missions
                }
                while pending:
                    done, pending = wait(
                        pending, return_when=FIRST_COMPLETED, timeout=0.5
                    )
                    for task in done:
                        # run_mission 内部已捕获所有已知异常，
                        # 这里消费 Future 以暴露未被捕获的异常并释放资源。
                        exc = task.exception()
                        if exc is not None:
                            self.appenv.say(f"[red]{_('任务发生未捕获异常：')}{exc}[/]")
                    if pending:
                        status.update(
                            _("正在执行{count}个任务...").format(count=len(pending))
                        )
