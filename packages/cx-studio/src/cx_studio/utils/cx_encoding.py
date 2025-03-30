from chardet import UniversalDetector

__char_detector = UniversalDetector()


def detect_encoding(filename):
    __char_detector.reset()
    try:
        with open(filename, "rb") as fp:
            for line in fp.readlines():
                __char_detector.feed(line)
                if __char_detector.done:
                    break
            result = __char_detector.result
            return result["encoding"]
    except FileNotFoundError:
        return "utf-8"
