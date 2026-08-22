__version__ = "1.0.0"

from .application import HostsKeeperApp
from .appcontext import HostsKeeperContext
from .appenv import appenv


def run():
    from rich.traceback import install
    import sys

    install(show_locals=False, word_wrap=True, suppress=["rich"])
    context = HostsKeeperContext.from_arguments(sys.argv[1:])
    with appenv:
        with HostsKeeperApp(
            appenv=appenv, context=context, progress=appenv.progress
        ) as app:
            app.run()
