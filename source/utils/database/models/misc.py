from typing import Any


class DictMixin:
    __slots__ = "_json"

    def __init__(self, **kwargs) -> None:
        self._json = {key: value for key, value in kwargs.items() if key in self.__slots__}

        for kwarg, value in kwargs.items():
            if kwarg in self.__slots__:
                setattr(self, kwarg, value)

        for slot in self.__slots__:
            if not slot.startswith("_") and slot not in kwargs:
                setattr(self, slot, None)

    def __repr__(self) -> str:
        kwargs = " ".join([f"{kwarg}={value}" for kwarg, value in self._json.items()])
        return f"<{self.__class__.__name__} {kwargs}>"

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)
        if not __name.startswith("_"):
            self._json[__name] = __value

    def __eq__(self, __o: object) -> bool:
        for slot in self.__slots__:
            if getattr(self, slot) != getattr(__o, slot):
                return False
        return True
