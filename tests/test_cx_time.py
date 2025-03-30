import unittest
from cx_studio.core.cx_time import CxTime
from cx_studio.core.cx_timebase import Timebase


class TestCxTime(unittest.TestCase):
    def test_initialization(self):
        time = CxTime(123456)
        self.assertEqual(time.total_milliseconds, 123456)
        self.assertEqual(time.milliseconds, 456)
        self.assertEqual(time.seconds, 3)
        self.assertEqual(time.minutes, 2)
        self.assertEqual(time.hours, 0)
        self.assertEqual(time.days, 0)

    def test_total_properties(self):
        time = CxTime(90061000)  # 1 day, 1 hour, 1 minute, 1 second
        self.assertEqual(time.total_seconds, 90061.0)
        self.assertEqual(time.total_minutes, 1501.0166666666667)
        self.assertEqual(time.total_hours, 25.016944444444444)
        self.assertEqual(time.total_days, 1.0423726851851852)

    def test_comparison(self):
        time1 = CxTime(1000)
        time2 = CxTime(2000)
        self.assertTrue(time1 < time2)
        self.assertTrue(time1 <= time2)
        self.assertTrue(time2 > time1)
        self.assertTrue(time2 >= time1)
        self.assertTrue(time1 != time2)
        self.assertTrue(time1 == CxTime(1000))

    def test_arithmetic_operations(self):
        time1 = CxTime(1000)
        time2 = CxTime(2000)
        self.assertEqual((time1 + time2).total_milliseconds, 3000)
        self.assertEqual((time2 - time1).total_milliseconds, 1000)
        self.assertEqual((time1 * 2).total_milliseconds, 2000)
        self.assertEqual((time2 / 2).total_milliseconds, 1000)

    def test_pretty_string(self):
        time = CxTime(90061000)  # 1 day, 1 hour, 1 minute, 1 second
        pretty = time.pretty_string
        self.assertIn("1日", pretty)
        self.assertIn("1小时", pretty)
        self.assertIn("1分", pretty)
        self.assertIn("1秒", pretty)

    def test_to_timestamp(self):
        time = CxTime(3661000)  # 1 hour, 1 minute, 1 second
        self.assertEqual(time.to_timestamp(), "01:01:01.000")

    def test_to_timecode(self):
        time = CxTime(3661000)  # 1 hour, 1 minute, 1 second
        timebase = Timebase(fps=30, drop_frame=False)
        self.assertEqual(time.to_timecode(timebase), "01:01:01:00")

    def test_from_timestamp(self):
        time = CxTime.from_timestamp("01:01:01.000")
        self.assertEqual(time.total_milliseconds, 3661000)

    def test_from_timecode(self):
        timebase = Timebase(fps=30, drop_frame=False)
        time = CxTime.from_timecode("01:01:01:00", timebase)
        self.assertEqual(time.total_milliseconds, 3661000)

    def test_class_methods(self):
        self.assertEqual(CxTime.zero().total_milliseconds, 0)
        self.assertEqual(CxTime.one_second().total_milliseconds, 1000)
        self.assertEqual(CxTime.from_seconds(1.5).total_milliseconds, 1500)
        self.assertEqual(CxTime.from_minutes(1.5).total_milliseconds, 90000)
        self.assertEqual(CxTime.from_hours(1.5).total_milliseconds, 5400000)
        self.assertEqual(CxTime.from_days(1.5).total_milliseconds, 129600000)


if __name__ == "__main__":
    unittest.main()
