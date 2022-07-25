from core import Asteroid, Language
from interactions import option  # noqa TODO: remove noqa
from interactions import Choice, CommandContext, Embed, Extension  # noqa TODO: remove noqa
from interactions import extension_command as command


class Misc(Extension):
    def __init__(self, client: Asteroid):
        self.client: Asteroid = client

    @command()
    @option(choices=[Choice(name=lang.name.lower().capitalize(), value=lang.value) for lang in Language])  # type: ignore
    async def language(self, ctx: CommandContext, language: str):
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        guild_data.settings.language = language
        await guild_data.settings.update()

        await ctx.send(f"Changed to {language}")


def setup(client):
    Misc(client)
