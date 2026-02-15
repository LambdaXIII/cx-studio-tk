from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence, Set, MutableMapping
from typing import Any
from warnings import deprecated


@deprecated
class DataPackage(MutableMapping):

    @staticmethod
    def __check_value(obj: Any) -> Any:
        if isinstance(obj, DataPackage):
            return obj
        if isinstance(obj, Mapping):
            return DataPackage(**obj)
        if isinstance(obj, Sequence | Set) and not isinstance(obj, str | bytes):
            return [DataPackage.__check_value(item) for item in obj]
        return obj

    def __init__(self, **kwargs):
        self.__internal_dict__: dict = {}
        for k, v in kwargs.items():
            self.__internal_dict__[k] = self.__check_value(v)

    def __len__(self):
        return self.__internal_dict__.__len__()

    def __iter__(self):
        return self.__internal_dict__.__iter__()

    def __get_value(self, key: Any) -> Any:
        if isinstance(key, str) and "." in key:
            k, *ks, last_k = key.split(".")
            v = self.__internal_dict__.get(k)
            for _k in ks:
                if v is None:
                    return None
                if isinstance(v, Mapping):
                    v = v.get(_k)
                elif isinstance(v, list):
                    try:
                        v = v[int(_k)]
                    except ValueError or IndexError:
                        v = None
            v = v.get(last_k) if isinstance(v, Mapping) else None
            return v
        return self.__internal_dict__.get(key)

    def __set_value(self, key: Any, value: Any) -> None:
        checked_value = self.__check_value(value)
        if isinstance(key, str) and "." in key:
            k, *ks, last_k = key.split(".")
            if not isinstance(self.__internal_dict__.get(k), MutableMapping):
                self.__internal_dict__[k] = DataPackage()
            current_obj = self.__internal_dict__[k]
            for _k in ks:
                if isinstance(current_obj, list):
                    try:
                        n = int(_k)
                        if not isinstance(current_obj[n], MutableMapping):
                            current_obj[n] = DataPackage()
                        current_obj = current_obj[n]
                    except ValueError or IndexError:
                        raise KeyError(f"{k}.{ks}" "is not a valid index")
                elif isinstance(current_obj, MutableMapping) and not isinstance(
                    current_obj.get(_k), MutableMapping
                ):
                    current_obj[_k] = DataPackage()
                current_obj = current_obj[_k]
            current_obj[last_k] = checked_value
        else:
            self.__internal_dict__[key] = checked_value

    def __del_value(self, key: Any):
        if isinstance(key, str) and "." in key:
            k, *ks, last_k = key.split(".")
            o = self.__internal_dict__.get(k)
            for _k in ks:
                if o is None:
                    return
                if isinstance(o, list):
                    try:
                        n = int(_k)
                        o = o[n]
                    except ValueError or IndexError:
                        o = None
                elif isinstance(o, MutableMapping):
                    o = o.get(_k)

            if o is None:
                return
            if isinstance(o, list):
                try:
                    n = int(last_k)
                    del o[n]
                except ValueError or IndexError:
                    pass
            elif isinstance(o, MutableMapping):
                del o[last_k]
        elif key in self.__internal_dict__:
            del self.__internal_dict__[key]

    def __getitem__(self, key: Any) -> Any:
        return self.__get_value(key)

    def __setitem__(self, key: Any, value: Any) -> None:
        self.__set_value(key, value)

    def __delitem__(self, key: Any) -> None:
        self.__del_value(key)

    def __contains__(self, key: Any) -> bool:
        return self.__get_value(key) is not None

    def get(self, key: Any, default: Any = None) -> Any:
        return self.__get_value(key) or default

    def keys(self):
        return self.__internal_dict__.keys()

    def values(self):
        return self.__internal_dict__.values()

    def items(self):
        return self.__internal_dict__.items()

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DataPackage):
            return False
        return self.__internal_dict__ == value.__internal_dict__

    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)

    def clear(self):
        self.__internal_dict__.clear()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self.__set_value(key, value)
        return self

    def pop(self, key: Any, default: Any = None) -> Any:
        return self.__internal_dict__.pop(key, default)

    def popitem(self) -> tuple[Any, Any]:
        return self.__internal_dict__.popitem()

    def setdefault(self, key: Any, default: Any = None) -> Any:
        return self.__internal_dict__.setdefault(key, default)

    def copy(self) -> DataPackage:
        return DataPackage(**self.__internal_dict__)

    def to_dict(self) -> dict:
        return {
            k: v.to_dict() if isinstance(v, DataPackage) else v
            for k, v in self.__internal_dict__.items()
        }

    def __getattribute__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return self.__get_value(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if (
            name.startswith("__")
            or name.startswith("_DataPackage__")
            or name in dir(self)
        ):
            object.__setattr__(self, name, value)
        else:
            self.__set_value(name, value)

    def __delattr__(self, name: str) -> None:
        try:
            object.__delattr__(self, name)
        except AttributeError:
            self.__del_value(name)

    def iter_all_keys(self) -> Iterable[str]:
        for k, v in self.__internal_dict__.items():
            yield k
            if isinstance(v, DataPackage):
                for _k in v.iter_all_keys():  # type: ignore
                    yield k + "." + _k
            if isinstance(v, list):
                for i, _k in enumerate(v):
                    yield k + "." + str(i)
                    if isinstance(_k, DataPackage):
                        for _k in _k.iter_all_keys():  # type: ignore
                            yield k + "." + str(i) + "." + _k

    def search(self, key: str) -> Iterable[Any]:
        for k in self.iter_all_keys():
            if k.endswith(key):
                yield self.__get_value(k)
