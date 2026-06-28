from abc import ABC, abstractmethod
from pathlib import Path

class IPathValidator(ABC):
    @abstractmethod
    def validate(self, path: str | Path) -> bool:
        pass


class ChainValidator(IPathValidator):
    def __init__(self, validators: list[IPathValidator] | None = None):
        self.__validators = validators or []

    def install(self, validator: IPathValidator):
        self.__validators.append(validator)
        return self

    def uninstall(self, validator: IPathValidator):
        self.__validators.remove(validator)
        return self

    def validate(self, path: str | Path) -> bool:
        return (
            True
            if len(self.__validators) == 0
            else all(v.validate(path) for v in self.__validators)
        )
