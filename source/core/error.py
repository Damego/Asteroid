from interactions import Permissions

__all__ = ["BotException", "MissingPermissions"]


class BotException(Exception):
    def __init__(self, code: int, **kwargs):
        self.code = code
        self.kwargs = kwargs

    @property
    def message(self):
        return {
            # Database errors
            1: "NAME_AND_AUTOROLE_MUTUALLY_EXCLUSIVE",
            2: "NAME_OR_AUTOROLE_REQUIRED",
            3: "AUTOROLE_NOT_FOUND",
            4: "NAME_AND_TAG_MUTUALLY_EXCLUSIVE",
            5: "NAME_OR_TAG_REQUIRED",
            6: "TAG_NOT_FOUND",
            7: "NAME_AND_EMOJIBOARD_MUTUALLY_EXCLUSIVE",
            8: "NAME_OR_EMOJIBOARD_REQUIRED",
            9: "EMOJIBOARD_NOT_FOUND",
            10: "USERID_AND_MUTUALLY_EXCLUSIVE",
            11: "USERID_OR_USER_REQUIRED",
            12: "USER_NOT_FOUND",
            # Autoroles errors
            100: "AUTOROLE_NOT_FOUND",
            101: "CHANNEL_NOT_FOUND",
            102: "MESSAGE_NOT_FOUND",
            103: "OPTION_NOT_FOUND",
            104: "OPTIONS_LIMIT",
            105: "BUTTONS_LIMIT",
            106: "BUTTON_NOT_FOUND",
            107: "ON_JOIN_ROLE_NOT_FOUND",
            108: "MESSAGE_WITHOUT_BUTTONS",
            109: "ROLE_ALREADY_EXIST",
            110: "NO_AUTO_ON_JOIN_ROLES",
            # Voice lobbies errors
            200: "VOICE_ALREADY_SETUP",
            201: "VOICE_NOT_SETUP",
            202: "DONT_HAVE_LOBBY",
            203: "CANT_UN_BLOCK_YOURSELF",
            204: "CANT_GIVE_OWNERSHIP_TO_SELF",
        }.get(self.code, f"Unknown Error with code: {self.code}")


class MissingPermissions(Exception):
    """Member doesn't have permissions to do an action."""

    def __init__(self, *permissions: Permissions):
        self.missed_permissions: tuple[Permissions] = permissions
