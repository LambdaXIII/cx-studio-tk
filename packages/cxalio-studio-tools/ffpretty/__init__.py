from .application import FFPrettyApp


def run():
    from rich.traceback import install

    install(show_locals=False, word_wrap=True, suppress=["rich"])

    with FFPrettyApp() as app:
        app.run()
