from datetime import datetime

from interactions import Choice, EmbedField, Extension, Modal, TextInput, TextStyleType
from interactions import extension_modal as modal
from interactions import option
from rapidfuzz import fuzz, process

from core import Asteroid, BotException, Language, Mention, TimestampMention, command, listener
from core.context import CommandContext
from core.database.models import GuildTag
from utils import create_embed



class Misc(Extension):
    def __init__(self, client):
        self.client: Asteroid = client

    @command()
    @option(
        description="The language to change",
        choices=[Choice(name=lang.name.lower().capitalize(), value=lang.value) for lang in Language],  # type: ignore
    )
    async def language(self, ctx: CommandContext, language: str):
        """Change language for bot on this server"""
        await ctx.defer(ephemeral=True)

        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        guild_data.settings.language = language
        await guild_data.settings.update()

        translate = ctx.translate("LANGUAGE_CHANGED")
        embed = create_embed(description=translate)
        await ctx.send(embeds=embed)

def setup(client):
    Misc(client)
