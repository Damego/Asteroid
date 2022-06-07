class DictMixin:  # ? Maybe use dataclass?
    __slots__ = "_json"

    def __init__(self, **kwargs) -> None:
        self._json = kwargs

        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)
