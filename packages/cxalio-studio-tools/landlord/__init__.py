from .application import LandlordApp


def run():
    with LandlordApp() as app:
        app.run()
