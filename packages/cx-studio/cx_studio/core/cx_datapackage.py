from collections import defaultdict


class DataPackage:
    def __init__(self, **kwargs):
        self._data = defaultdict(DataPackage)
        for key, value in kwargs.items():
            if isinstance(value, dict):
                self._data[key] = DataPackage(**value)
            else:
                self._data[key] = value

    def __getitem__(self, key):
        if isinstance(key, str) and "." in key:
            keys = key.split(".")
            current = self._data
            for k in keys:
                current = current[k]
            return current
        else:
            return self._data.get(key, None)  # 返回 None 如果键不存在

    def __setitem__(self, key, value):
        if isinstance(key, str) and "." in key:
            keys = key.split(".")
            current = self._data
            for k in keys[:-1]:
                if not isinstance(current[k], DataPackage):
                    current[k] = DataPackage()
                current = current[k]
            current[keys[-1]] = value
        else:
            self._data[key] = value

    def __delitem__(self, key):
        if isinstance(key, str) and "." in key:
            keys = key.split(".")
            current = self._data
            for k in keys[:-1]:
                if not isinstance(current[k], DataPackage):
                    raise KeyError(f"No such key: {'.'.join(keys)}")
                current = current[k]
            del current[keys[-1]]
        else:
            if key in self._data:
                del self._data[key]
            else:
                raise KeyError(f"No such key: {key}")

    def __getattr__(self, key):
        if key in self._data:
            return self._data[key]
        return None  # 返回 None 如果属性不存在

    def __setattr__(self, key, value):
        if key == "_data":
            super().__setattr__(key, value)
        else:
            if isinstance(value, dict):
                value = DataPackage(**value)
            self._data[key] = value

    def search(self, key):
        """递归搜索指定键并返回对应的值（支持嵌套结构）"""
        for k, value in self._data.items():
            if k == key:
                yield value
            if isinstance(value, DataPackage):
                yield from value.search(key)  # 递归搜索子元素

    def deep_search(self, key):
        """递归搜索指定键并返回对应的值（支持嵌套结构和非DataPackage对象）"""
        for k, value in self._data.items():
            if k == key:
                yield value
            if isinstance(value, DataPackage):
                yield from value.deep_search(key)  # 递归搜索子元素
            elif hasattr(value, key):  # 检查非DataPackage对象是否包含key属性
                yield getattr(value, key)

    def to_dict(self):
        result = {}
        for key, value in self._data.items():
            if isinstance(value, DataPackage):
                result[key] = value.to_dict()  # 递归处理嵌套 DataPackage
            else:
                result[key] = value
        return result

    def update(self, other: "DataPackage|dict"):
        if not isinstance(other, (DataPackage, dict)):
            raise TypeError("other must be DataPackage or dict")
        other = DataPackage(**other) if isinstance(other, dict) else other
        self._data.update(other._data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"
