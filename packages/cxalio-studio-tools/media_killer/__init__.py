import sys

from .application import Application


def run():
    with Application() as app:
        app.run()
