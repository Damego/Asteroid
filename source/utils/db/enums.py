from enum import Enum


class OperatorType(Enum):
    """
    Class representing operator types in MongoDB
    """

    SET = "$set"
    UNSET = "$unset"
    PUSH = "$push"
    PULL = "$pull"
    EACH = "$each"
    RENAME = "$rename"
    INC = "$inc"


class Document(Enum):
    CONFIGURATION = "configuration"
    PRIVATE_VOICE = "private_voice"
    VOICE_TIME = "voice_time"
    AUTOROLE = "autorole"
    STARBOARD = "starboard"
    TAGS = "tags"
    COGS_DATA = "cogs_data"
    ROLES_BY_LEVEL = "roles_by_level"


class CollectionType(Enum):
    CONFIGURATION = "configuration"
    USERS = "users"
