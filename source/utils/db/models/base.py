from typing import Any


class DictMixin:  # ? Maybe use dataclass?
    __slots__ = "_json"

    def __init__(self, **kwargs) -> None:
        self._json = {key: value for key, value in kwargs.items() if key in self.__slots__}

        for kwarg, value in kwargs.items():
            if kwarg in self.__slots__:
                setattr(self, kwarg, value)

    def __repr__(self) -> str:
        kwargs = " ".join([f"{kwarg}={value}" for kwarg, value in self._json.items()])
        return f"<{self.__class__.__name__} {kwargs}>"

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name == "_json":
            return
        super().__setattr__(__name, __value)
        self._json[__name] = __value
