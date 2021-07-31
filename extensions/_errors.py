from discord.ext.commands import CommandError

class TagNotFound(CommandError):
    pass

class ForbiddenTag(CommandError):
    pass

class UIDNotBinded(CommandError):
    pass

class AccountHidden(CommandError):
    pass