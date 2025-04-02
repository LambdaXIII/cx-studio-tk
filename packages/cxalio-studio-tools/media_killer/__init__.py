from .application import Application


def main():
    with Application() as app:
        app.run()
