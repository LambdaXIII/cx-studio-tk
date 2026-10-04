"""subtitler —— 字幕格式互转工具。

工具顶只保留版本号与导入入口，可复用的字幕能力位于 ``subtitler.common``：
模型（Item/Sequence/Project）、格式框架（Loader/Saver/Format）与各格式实现。

`run()` 是 `[project.scripts]` 的入口：应用栈（cx_tools/cx_wealthy/argparse）
的 import 全部下沉到函数体内，使模块级导入零框架依赖——只 import 本模块即可
取用 ``__version__`` 与 ``run``，而不会连带加载前台框架。
"""

import sys

__version__: str = "1.3.0"


def run() -> None:
    """启动 subtitler 命令行工具。"""
    from rich.traceback import install

    from cx_tools.app import SafeError

    from .application import SubtitlerApplication
    from .appcontext import SubtitlerContext
    from .appenv import SubtitlerEnv

    install(show_locals=False, word_wrap=True, suppress=["rich"])
    appenv = SubtitlerEnv()
    try:
        context = SubtitlerContext.from_arguments(sys.argv[1:])
    except SafeError as e:
        appenv.say(f"[{e.style}]{e}[/]")
        return
    with appenv:
        with SubtitlerApplication(appenv=appenv, context=context) as app:
            app.run()
