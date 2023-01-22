from .database.consts import StrEnum

__all__ = ["Mention", "TimestampMention"]


class Mention(StrEnum):
    """
    Representing strings to mention role/member/etc.
    """

    USER = "<@{id}>"
    ROLE = "<@&{id}>"
    CHANNEL = "<#{id}>"
    COMMAND = "</{name}:{id}>"


class TimestampMention(StrEnum):
    SHORT_TIME = "<t:{0}:t>"
    LONG_TIME = "<t:{0}:T>"
    SHORT_DATE = "<t:{0}:d>"
    LONG_DATE = "<t:{0}:D>"
    SHORT = "<t:{0}:f>"
    LONG = "<t:{0}:F>"
    RELATIVE = "<t:{0}:R>"
