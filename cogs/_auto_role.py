from discord import Embed
from discord.ext import commands
from discord_slash import SlashContext
from discord_slash.cog_ext import (
    cog_slash as slash_command,
    cog_subcommand as slash_subcommand
)
from discord_components import Select, SelectOption, Button, ButtonStyle
from discord_slash_components_bridge import ComponentContext

from my_utils import (
    AsteroidBot,
    LANGUAGES_LIST,
    get_content,
    is_administrator_or_bot_owner,
    Cog
)
from .settings import guild_ids


class AutoRole(Cog):
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.name = 'AutoRole'


    @slash_subcommand(
        base='autorole',
        name='send',
        guild_ids=guild_ids
    )
    async def autorole_send_message(self, ctx: SlashContext, name: str):
        ...

    @slash_subcommand(
        base='autorole',
        name='add',
        guild_ids=guild_ids
    )
    async def autorole_add(self, ctx: SlashContext, name: str):
        ...

    @slash_subcommand(
        base='autorole',
        name='remove',
        guild_ids=guild_ids
    )
    async def autorole_remove(self, ctx: SlashContext, name: str):
        ...

