__version__ = "0.9.0"

from .application import HostsKeeperApp
from .appcontext import AppContext
from .appenv import appenv


def run():
    from rich.traceback import install
    import sys

    install(show_locals=False, word_wrap=True, suppress=["rich"])
    context = AppContext.from_arguments(sys.argv[1:])
    with appenv:
        with HostsKeeperApp(
            appenv=appenv, context=context, progress=appenv.progress
        ) as app:
            app.run()
