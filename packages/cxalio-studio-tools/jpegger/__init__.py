from .simple_application import JpeggerApp


def run():
    from rich.traceback import install

    install(show_locals=False, word_wrap=True, suppress=["rich"])
    with JpeggerApp() as app:
        app.run()
