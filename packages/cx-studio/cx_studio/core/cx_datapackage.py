from collections import defaultdict
from typing import Union


class DataPackage:
    """_summary_
    数据包装类，用于包装数据，支持字典和属性访问
    """

    def __init__(self, **kwargs):
        self.__data = defaultdict(DataPackage)
        for k, v in kwargs.items():
            self.__data[k] = DataPackage.__check_value(v)

    def update(self, other: Union[dict, "DataPackage"]):
        if not isinstance(other, (dict, DataPackage)):
            raise TypeError("other must be dict or DataPackage")
        data = (
            other
            if isinstance(other, DataPackage)
            else DataPackage.__check_value(other)
        )
        self.__data.update(data.__data)

    @classmethod
    def from_dict(cls, data: dict):
        result = cls()
        for k, v in data.items():
            result.__data[k] = DataPackage.__check_value(v)
        return result

    @staticmethod
    def __check_value(value):
        if isinstance(value, list):
            return [DataPackage.__check_value(v) for v in value]
        elif isinstance(value, dict):
            return DataPackage.from_dict(value)
        else:
            return value

    def __getattr__(self, key):
        return self.__data.get(key, None)

    def __setattr__(self, key, value):
        if key == "_DataPackage__data":
            object.__setattr__(self, key, value)
        else:
            self.__data[key] = DataPackage.__check_value(value)

    def __locate_item(self, address: str | list[str]):
        if isinstance(address, str):
            address = address.split(".")
        item = self.__data.get(address[0], None)
        for k in address[1:]:
            if item is None:
                break
            item = item.__getattr__(k)
        return item

    def __getitem__(self, key):
        if isinstance(key, str) and ("." in key):
            keys = key.split(".")
            item = self.__data.get(keys[0], None)
            for k in keys[1:]:
                if item is None:
                    break
                item = item.__getattr__(k)
            return item
        return self.__data[key]

    def __setitem__(self, key, value):
        if isinstance(key, str) and ("." in key):
            keys = key.split(".")
            next_keys = ".".join(keys[1:])
            self.__data[keys[0]].__setitem__(next_keys, value)
        else:
            self.__data[key] = DataPackage.__check_value(value)

    def __rich_repr__(self):
        yield "DataPackage"
        for k, v in self.__data.items():
            yield k, v

    def to_dict(self) -> dict:
        result = {}
        for k, v in self.__data.items():
            value = v.to_dict() if isinstance(v, DataPackage) else v
            result[k] = value
        return result
