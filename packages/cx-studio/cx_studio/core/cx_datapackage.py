from collections.abc import Generator

from cx_studio.utils import NumberUtils


class DataPackage:
    def __init__(self, *args, **kwargs):
        self.__data = {}
        for k, v in kwargs.items():
            if k in self.__dict__:
                object.__setattr__(self, k, v)
            else:
                self.__data[k] = self._check_value(v)

    @classmethod
    def _check_value(cls, value):
        if isinstance(value, cls):
            pass
        elif isinstance(value, list | tuple | set):
            return [cls._check_value(x) for x in value]
        elif isinstance(value, dict):
            return cls(**value)
        return value

    @staticmethod
    def __get_value(obj, key):
        if isinstance(obj, DataPackage):
            return (
                object.__getattribute__(obj, key)
                if key in obj.__dict__
                else obj.__data.get(key)
            )
        elif isinstance(key, int) and isinstance(obj, list):
            return obj[key] if 0 <= key <= len(obj) else None
        elif isinstance(obj, dict):
            return obj.get(key)
        return None

    @staticmethod
    def __contains_key(obj, key) -> bool:
        return DataPackage.__get_value(obj, key) is not None

    @staticmethod
    def __set_value(obj, key, value):
        if isinstance(obj, DataPackage):
            if key in obj.__dict__:
                object.__setattr__(obj, key, value)
            else:
                obj.__data[key] = value
        elif isinstance(key, int) and isinstance(obj, list):
            index = int(NumberUtils.limit_number(key, bottom=0, top=len(obj) - 1))
            obj[index] = value
        elif isinstance(obj, dict):
            obj[key] = value
        else:
            raise TypeError("Cannot set value for object of type {}".format(type(obj)))

    def __getattr__(self, item):
        return self.__data.get(item)

    def __setattr__(self, key, value):
        if key in self.__dict__ or key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self.__data[key] = self._check_value(value)

    def __getitem__(self, item):
        if isinstance(item, str) and "." in item:
            key, *sub_keys, final_key = item.split(".")
            current = DataPackage.__get_value(self, key)
            for k in sub_keys:
                current = DataPackage.__get_value(current, k)
                if current is None:
                    return None
            return DataPackage.__get_value(current, final_key)
        return DataPackage.__get_value(self, item)

    def __setitem__(self, key, value):
        if key in self.__dict__:
            object.__setattr__(self, key, value)
        elif isinstance(key, str) and "." in key:
            *keys, final_key = key.split(".")
            current = self
            for k in keys:
                x = DataPackage.__get_value(current, k)
                if not isinstance(x, DataPackage | dict):
                    DataPackage.__set_value(current, k, DataPackage())
                current = DataPackage.__get_value(current, k)
            current[final_key] = value  # type: ignore
        else:
            self.__data[key] = self._check_value(value)

    def __delitem__(self, key):
        if key in self.__dict__:
            raise TypeError("'{}' is an attribute, not a data key.".format(key))
        if isinstance(key, str) and "." in key:
            *keys, final_key = key.split(".")
            current = self
            for k in keys:
                current = DataPackage.__get_value(current, k)
                if current is None:
                    raise KeyError("Key '{}' not found.".format(key))
            del current[final_key]
        else:
            del self.__data[key]

    def __contains__(self, item):
        if isinstance(item, str) and "." in item:
            *keys, final_key = item.split(".")
            current = self
            for k in keys:
                current = DataPackage.__get_value(current, k)
                if current is None:
                    return False
            return DataPackage.__contains_key(current, final_key)
        else:
            return DataPackage.__contains_key(self, item)

    def keys(self) -> list:
        safe_keys = [k for k in self.__dict__ if not str(k).startswith("_")]
        data_keys = self.__data.keys()
        return safe_keys + list(data_keys)

    def __iter__(self):
        for k in self.__dict__:
            if not k.startswith("_"):
                yield k
        yield from self.__data

    def __len__(self):
        return sum(1 for k in self.__iter__())

    def items(self) -> Generator[tuple, None, None]:
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
                yield k, v
        yield from self.__data.items()

    def get(self, key):
        return self.__getitem__(key)

    def values(self):
        for k in self.keys():
            yield self.__getitem__(k)

    def update(self, other: "DataPackage|dict|None" = None, **kwargs):
        if isinstance(other, (DataPackage, dict)):
            for k, v in other.items():
                self[k] = self._check_value(v)
        elif other is None:
            pass
        else:
            raise TypeError(
                "Cannot update DataPackage with object of type {}. "
                "Maybe try to unpack it or make it a dict.".format(type(other))
            )

        for k, v in kwargs.items():
            self[k] = self._check_value(v)

    def clear(self):
        self.__data.clear()

    def search(self, key) -> Generator:
        # TODO: support '.' keys
        for k, v in self.items():
            if k == key:
                yield v
            if isinstance(v, DataPackage):
                yield from v.search(key)
            elif isinstance(v, dict) and k in v:
                yield v[k]

    def to_dict(self) -> dict:
        result = {}
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
                result[k] = v

        for k, v in self.__data.items():
            value = v
            if isinstance(v, DataPackage):
                value = v.to_dict()
            elif isinstance(v, list):
                value = [x.to_dict() if isinstance(x, DataPackage) else x for x in v]
            result[k] = value

        return result

    def __rich_repr__(self):
        yield from self.items()
