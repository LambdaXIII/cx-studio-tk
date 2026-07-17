__version__ = "0.8.6"

from .application import Application


def run():
    from rich.traceback import install

    install(show_locals=True)
    with Application() as app:
        app.run()
