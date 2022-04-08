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