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

    def test_nested_key_access(self):
        dp = DataPackage()
        dp.a = 12
        self.assertEqual(dp["a"], 12)
        dp["a.b"] = 33
        self.assertEqual(dp["a.b"], 33)
        self.assertIsInstance(dp.a, DataPackage)
        dp["a.b.c"] = 10
        self.assertEqual(dp.a.b.c, 10)
        self.assertEqual(dp["a.b"].c, 10)

    def test_nested_key_assignment(self):
        dp = DataPackage()
        dp["a.b.c"] = 1
        self.assertEqual(dp.a.b.c, 1)
        dp["a.b.d"] = 2
        self.assertEqual(dp.a.b.d, 2)
        dp["a.e"] = 3
        self.assertEqual(dp.a.e, 3)

    def test_invalid_update(self):
        dp = DataPackage()
        with self.assertRaises(TypeError):
            dp.update(123)

    def test_nested_search(self):
        data = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3,
            },
            "e": {"c": 3, "d": 4},
        }
        dp = DataPackage(**data)
        result = list(dp.search("c"))
        self.assertListEqual(result, [2, 3])
        result = list(dp.search("d"))
        self.assertListEqual(result, [3, 4])


if __name__ == "__main__":
    unittest.main()
