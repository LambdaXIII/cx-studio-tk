import pytest
from collections.abc import Mapping, MutableMapping
from cx_studio.core import DataPackage


class TestDataPackage:
    test_dict: dict = {
        "name": "John",
        "age": 38,
        "male": True,
        "address": {
            "street": "Main Street",
            "city": "New York",
            "state": "NY",
            "zip": "10001",
        },
        "phone": [
            {"type": "home", "number": "555-555-5555"},
            {"type": "work", "number": "555-555-5556"},
        ],
        "email": ["john.doe@example.com", "john.doe@example.net"],
    }

    def test_types(self):
        dp = DataPackage()
        assert isinstance(dp, DataPackage)
        assert isinstance(dp, Mapping)
        assert isinstance(dp, MutableMapping)

    def test_init(self):
        dp = DataPackage(**self.test_dict)
        assert isinstance(dp["address"], DataPackage)
        assert isinstance(dp["phone"], list)
        assert isinstance(dp["email"], list)

    def test_getitem(self):
        dp = DataPackage(**self.test_dict)
        assert dp["name"] == "John"
        assert dp["age"] == 38
        assert dp["male"] is True
        assert dp["address"]["street"] == dp["address.street"] == "Main Street"
        assert dp["address"]["city"] == dp["address.city"] == "New York"
        assert dp["phone"][0]["number"] == "555-555-5555"
        assert dp["phone.1.number"] == "555-555-5556"

    def test_getattribute(self):
        dp = DataPackage(**self.test_dict)
        assert dp.name == "John"
        assert dp.age == 38
        assert dp.male is True
        assert dp.address.street == "Main Street"
        assert dp.address.city == "New York"
        assert dp.phone[0].number == "555-555-5555"

    def test_keys(self):
        dp = DataPackage(**self.test_dict)
        assert list(dp.keys()) == [
            "name",
            "age",
            "male",
            "address",
            "phone",
            "email",
        ]
        all_keys = list(dp.iter_all_keys())
        expected_all_keys = [
            "name",
            "age",
            "male",
            "address",
            "address.street",
            "address.city",
            "address.state",
            "address.zip",
            "phone",
            "phone.0",
            "phone.0.type",
            "phone.0.number",
            "phone.1",
            "phone.1.type",
            "phone.1.number",
            "email",
            "email.0",
            "email.1",
        ]
        assert all_keys == expected_all_keys

    def test_set_item(self):
        dp = DataPackage()
        dp["name"] = "John"
        assert dp["name"] == "John"
        dp.name = "Jane"
        assert dp["name"] == "Jane"
        dp["address.street"] = "Main Street"
        assert dp["address.street"] == "Main Street"
        dp.address.street = "Main Street"
        assert dp["address.street"] == "Main Street"
