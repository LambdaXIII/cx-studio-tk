__version__ = "1.0.0"

import sys

from .appcontext import FFPrettyContext
from .application import FFPrettyApp
from .appenv import appenv


def run():
    from rich.traceback import install
    from cx_tools.app import SafeError

    install(show_locals=False, word_wrap=True, suppress=["rich"])

    with appenv:
        try:
            context = FFPrettyContext.from_arguments(sys.argv[1:])
        except SafeError as e:
            appenv.say(f"[{e.style}]{e}[/]")
            return
        with FFPrettyApp(
            appenv=appenv, context=context, progress=appenv.progress
        ) as app:
            app.run()
    return None
