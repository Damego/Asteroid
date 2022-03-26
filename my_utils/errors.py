class BotNotConnectedToVoice(Exception):
    pass


class NotConnectedToVoice(Exception):
    pass


class NotPlaying(Exception):
    pass


class TagNotFound(Exception):
    pass


class ForbiddenTag(Exception):
    pass


class NotTagOwner(Exception):
    pass


class TagsIsPrivate(Exception):
    pass


class UIDNotBinded(Exception):
    pass


class CogDisabledOnGuild(Exception):
    pass


class CommandDisabled(Exception):
    """For disabled commands for guild"""

    def __init__(self, message: str = None):
        self.message = message


class NoData(Exception):
    """Nothing found in database"""

class NotGuild(Exception):
    """Raises when guild is None"""
