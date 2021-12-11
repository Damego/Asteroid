from discord.ext.commands import Converter, BadArgument

multiplier = {
    'д': 86400,
    'ч': 3600,
    'м': 60,
    'с': 1,
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1
}

class DurationConverter(Converter):
    async def convert(self, ctx, argument):
        amount = argument[:-1]
        time_format = argument[-1]

        if amount.isdigit() and time_format in ['д', 'ч', 'м', 'с', 'd', 'h', 'm', 's']:
            return (int(amount), time_format)

        raise BadArgument(message='Wrong time format!')