from cx_studio.core import CxTime


class TestCxTime:
    def test_creation(self):
        time = CxTime()
        assert time is not None
