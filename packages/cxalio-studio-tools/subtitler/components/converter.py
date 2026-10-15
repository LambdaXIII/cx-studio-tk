"""subtitler 转换编排。

`SubtitlerConverter` 把一次转换串成一条线：按文件扩展名经 `wiring` 查表确定
源/目标格式 → Loader 从来源提取 Item → 逐个路由进 `SubtitleProject` → Saver
把工程条目集合以目标格式写出 → 逐条呈现实际产出的文件路径。

工具只搬运模型，不对字幕内容施加编辑、修剪或重排；失败统一转 `SafeError`
呈现给用户，不写出部分输出。
"""

from cx_tools.app import IAppComponent, IAppEnvironment, SafeError

from subtitler.common import FormatError, SubtitleProject
from subtitler.i18n import _

from ..appcontext import SubtitlerContext
from .wiring import format_for


class SubtitlerConverter(IAppComponent):
    """执行一次字幕格式转换的前台编排组件。

    Args:
        appenv: 应用环境实例。
        context: 命令行上下文，提供输入/输出路径。
    """

    def __init__(self, appenv: IAppEnvironment, context: SubtitlerContext) -> None:
        super().__init__(appenv, context)
        self.appenv = appenv
        self.context = context

    def convert(self) -> None:
        """按上下文给出的路径执行一次转换并呈现产出。

        源与目标格式按文件扩展名查表；读入或写出失败报错中止，不产生部分输出。

        Raises:
            SafeError: 扩展名未识别，或读入/写出失败。
        """
        source = self.context.input
        target = self.context.output
        # 上下文解析已保证非 help 路径下二者在场。
        assert source is not None and target is not None

        source_format = format_for(source)
        if source_format is None:
            raise SafeError(_("无法识别的文件扩展名: {path}").format(path=source))
        target_format = format_for(target)
        if target_format is None:
            raise SafeError(_("无法识别的文件扩展名: {path}").format(path=target))

        try:
            items = source_format.loader.load(source)
        except (FormatError, OSError) as exc:
            raise SafeError(_("读入失败: {error}").format(error=exc)) from exc

        project = SubtitleProject()
        for item in items:
            project.add(item)

        try:
            produced = target_format.saver.save(project, target)
        except (FormatError, OSError) as exc:
            raise SafeError(_("写出失败: {error}").format(error=exc)) from exc

        for path in produced:
            self.appenv.say(f"[cx.success]{_('已写出')}[/] [cx.info]{path}[/]")
