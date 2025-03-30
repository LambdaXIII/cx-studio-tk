import unittest
from cx_studio.core.cx_filesize import FileSize


class TestFileSize(unittest.TestCase):
    def test_initialization(self):
        self.assertEqual(FileSize(1024).total_bytes, 1024)
        self.assertEqual(FileSize(-1).total_bytes, 0)

    def test_from_methods(self):
        self.assertEqual(FileSize.from_bytes(1024).total_bytes, 1024)
        self.assertEqual(FileSize.from_kilobytes(1).total_bytes, 1024)
        self.assertEqual(FileSize.from_megabytes(1).total_bytes, 1024**2)
        self.assertEqual(FileSize.from_gigabytes(1).total_bytes, 1024**3)
        self.assertEqual(FileSize.from_terabytes(1).total_bytes, 1024**4)
        self.assertEqual(FileSize.from_petabytes(1).total_bytes, 1024**5)
        self.assertEqual(FileSize.from_exabytes(1).total_bytes, 1024**6)

    def test_total_properties(self):
        size = FileSize(1024**3)  # 1 GiB
        self.assertEqual(size.total_kilobytes, 1024**2)
        self.assertEqual(size.total_megabytes, 1024)
        self.assertEqual(size.total_gigabytes, 1)
        self.assertEqual(size.total_terabytes, 1 / 1024)
        self.assertEqual(size.total_petabytes, 1 / 1024**2)
        self.assertEqual(size.total_exabytes, 1 / 1024**3)

    def test_pretty_string(self):
        self.assertEqual(FileSize(1024).pretty_string, "1.00 KB")
        self.assertEqual(FileSize(1024**2).pretty_string, "1.00 MB")
        self.assertEqual(FileSize(1024**3).pretty_string, "1.00 GB")
        self.assertEqual(FileSize(500).pretty_string, "500 B")

    def test_comparison_operators(self):
        size1 = FileSize(1024)
        size2 = FileSize(2048)
        self.assertTrue(size1 < size2)
        self.assertTrue(size1 <= size2)
        self.assertTrue(size2 > size1)
        self.assertTrue(size2 >= size1)
        self.assertTrue(size1 == FileSize(1024))
        self.assertTrue(size1 != size2)

    def test_arithmetic_operations(self):
        size1 = FileSize(1024)
        size2 = FileSize(2048)
        self.assertEqual((size1 + size2).total_bytes, 3072)
        self.assertEqual((size2 - size1).total_bytes, 1024)
        self.assertEqual((size1 * 2).total_bytes, 2048)
        self.assertEqual((size2 / 2).total_bytes, 1024)

    def test_invalid_operations(self):
        size = FileSize(1024)
        with self.assertRaises(NotImplementedError):
            size + 100
        with self.assertRaises(NotImplementedError):
            size - "string"
        with self.assertRaises(NotImplementedError):
            size < "string"
        with self.assertRaises(NotImplementedError):
            size * "string"
        with self.assertRaises(NotImplementedError):
            size / "string"


if __name__ == "__main__":
    unittest.main()
