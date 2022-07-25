from .database.consts import StrEnum

__all__ = ["Mentions"]


class Mentions(StrEnum):
    """
    Representing strings to mention role/member/etc.
    """

    USER = "<@{id}>"
    ROLE = "<@&{id}>"
    CHANNEL = "<#{id}>"
    COMMAND = "</{name}:{id}>"
