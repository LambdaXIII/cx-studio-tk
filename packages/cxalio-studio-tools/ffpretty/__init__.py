from .application import FFPrettyApp


def run():
    from rich.traceback import install

    install(show_locals=False, word_wrap=True, suppress=["rich"])

    with FFPrettyApp() as app:
        result = app.run()
        return 0 if result else -1
    return None
