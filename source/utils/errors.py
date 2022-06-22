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


class PrivateVoiceNotSetup(Exception):
    """Guild dont have enabled private voice"""


class DontHavePrivateRoom(Exception):
    """Member doesnt have private room"""


class MessageWithoutAutoRole(Exception):
    ...


class AutoRoleNotFound(Exception):
    ...


class OptionsOverKill(Exception):
    ...


class OptionNotFound(Exception):
    ...


class OptionLessThanOne(Exception):
    ...


class NotSavedAutoRoles(Exception):
    ...


class NotDropDown(Exception):
    ...


class NotButton(Exception):
    ...


class LabelOrEmojiRequired(Exception):
    ...


class ButtonsOverKill(Exception):
    ...


class DuplicateRole(Exception):
    ...


class AutoRoleAlredyExists(Exception):
    ...


class NoteAlreadyExist(Exception):
    ...
