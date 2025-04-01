import logging

from .appserver import server


class Application:
    def __init__(self):
        pass

    def __enter__(self):
        server.start_environment()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        server.stop_environment()
        return False

    def run(self):
        server.say("I am the best!")
        server.say(server.context)
