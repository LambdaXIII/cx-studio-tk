__version__ = "0.8.7"

from .application import MediaScoutApp
from .appcontext import MediaScoutContext
from .appenv import MediaScoutEnv


def run():
    from rich.traceback import install

    install(show_locals=True)
    context = MediaScoutContext.load()
    appenv = MediaScoutEnv()
    with appenv:
        with MediaScoutApp(appenv=appenv, context=context) as app:
            app.run()
