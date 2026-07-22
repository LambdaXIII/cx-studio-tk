__version__ = "0.10.0"

import os


def get_root():
    return os.path.abspath(os.path.dirname(__file__))
