import unittest
from cx_studio.core.cx_datapackage import DataPackage


class TestDataPackage(unittest.TestCase):
    def test_initialization(self):
        dp = DataPackage(a=1, b={"c": 2, "d": [3, 4]})
        self.assertEqual(dp.a, 1)
        self.assertEqual(dp.b.c, 2)
        self.assertEqual(dp.b.d, [3, 4])

    def test_update_with_dict(self):
        dp = DataPackage(a=1)
        dp.update({"b": 2, "c": {"d": 3}})
        self.assertEqual(dp.b, 2)
        self.assertEqual(dp.c.d, 3)

    def test_update_with_datapackage(self):
        dp1 = DataPackage(a=1)
        dp2 = DataPackage(b=2, c={"d": 3})
        dp1.update(dp2)
        self.assertEqual(dp1.b, 2)
        self.assertEqual(dp1.c.d, 3)

    def test_from_dict(self):
        data = {"a": 1, "b": {"c": 2, "d": [3, 4]}}
        dp = DataPackage.from_dict(data)
        self.assertEqual(dp.a, 1)
        self.assertEqual(dp.b.c, 2)
        self.assertEqual(dp.b.d, [3, 4])

    def test_nested_key_access(self):
        dp = DataPackage(a={"b": {"c": 1}})
        self.assertEqual(dp["a.b.c"], 1)

    def test_nested_key_assignment(self):
        dp = DataPackage()
        dp["a.b.c"] = 1
        self.assertEqual(dp.a.b.c, 1)

    def test_invalid_update(self):
        dp = DataPackage()
        with self.assertRaises(TypeError):
            dp.update(123)


if __name__ == "__main__":
    unittest.main()
