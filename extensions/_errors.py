from discord.ext.commands import CommandError

class NotConnectedToVoice(CommandError):
    pass

class TagNotFound(CommandError):
    pass

class ForbiddenTag(CommandError):
    pass

class NotTagOwner(CommandError):
    pass

class UIDNotBinded(CommandError):
    pass

class GenshinDataNotPublic(CommandError):
    pass

class GenshinAccountNotFound(CommandError):
    pass
