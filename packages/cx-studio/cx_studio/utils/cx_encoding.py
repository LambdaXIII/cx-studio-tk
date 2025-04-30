from chardet import UniversalDetector
from lazy_object_proxy import Proxy

__char_detector = Proxy(UniversalDetector)


def detect_encoding(filename, default_encoding: str | None = "utf-8"):
    __char_detector.reset()
    try:
        with open(filename, "rb") as fp:
            max_len = 200 * 1024 * 20
            while not __char_detector.done and max_len > 0:
                line = fp.read(200 * 1024)
                if line == b"":
                    break
                __char_detector.feed(line)
                max_len -= len(line)
            result = __char_detector.result
            return result["encoding"]
    except FileNotFoundError:
        return default_encoding or "locale"
