import unittest
from unittest.mock import Mock
from cx_studio.tag_replacer.cx_tagreplacer import TagReplacer
from cx_studio.tag_replacer.cx_tagpattern import TagPattern


class TestTagReplacer(unittest.TestCase):

    def setUp(self):
        self.mock_pattern = Mock(spec=TagPattern)
        self.mock_pattern.regex_pattern = r"\{\{(\w+)(?::(.*?))?\}\}"
        self.mock_pattern.parse = Mock(
            side_effect=lambda match: (match.group(1), match.group(2))
        )
        self.replacer = TagReplacer(tag_pattern=self.mock_pattern)

    def test_install_and_get_provider(self):
        provider = lambda x: f"Hello {x}"
        self.replacer.install_provider("greet", provider)
        self.assertEqual(self.replacer.get_provider("greet"), provider)

    def test_remove_provider(self):
        self.replacer.install_provider("key", "value")
        self.replacer.remove_provider("key")
        self.assertIsNone(self.replacer.get_provider("key"))

    def test_replace_with_callable_provider(self):
        self.replacer.install_provider("greet", lambda name: f"Hello {name}")
        source = "Welcome {{greet:John}}!"
        self.mock_pattern.parse = Mock(return_value=("greet", "John"))
        result = self.replacer.replace(source)
        self.assertEqual(result, "Welcome Hello John!")

    def test_replace_with_static_provider(self):
        self.replacer.install_provider("site", "example.com")
        source = "Visit {{site}} for more info."
        self.mock_pattern.parse = Mock(return_value=("site", None))
        result = self.replacer.replace(source)
        self.assertEqual(result, "Visit example.com for more info.")

    def test_replace_with_missing_provider(self):
        source = "Unknown {{missing}} tag."
        self.mock_pattern.parse = Mock(return_value=("missing", None))
        result = self.replacer.replace(source)
        self.assertEqual(result, "Unknown {{missing}} tag.")


if __name__ == "__main__":
    unittest.main()
