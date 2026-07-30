__version__ = "0.8.6"

from .application import MediaScoutApp
from .appenv import AppEnv
from .arg_parser import AppContext


def run():
    from rich.traceback import install

    install(show_locals=True)
    context = AppContext.load()
    appenv = AppEnv()
    with appenv:
        with MediaScoutApp(appenv=appenv, context=context) as app:
            app.run()
