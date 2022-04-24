from datetime import datetime, timedelta, timezone
from typing import Union

from aiohttp import ClientSession
from discord import Intents
from discord.ext.commands import Bot
from discord_slash import MenuContext, SlashCommand, SlashContext
from github import Github
from utils.database.mongo import Mongo


class AsteroidBot(Bot):
    def __init__(self, *, mongodb_token: str, github_token: str, repo_name: str):
        super().__init__(command_prefix="asteroid!", intents=Intents.all())
        self.__default_invite_link = None
        self.mongo = Mongo(mongodb_token)
        self.slash = SlashCommand(self, sync_commands=False, sync_on_cog_reload=False)

        today = datetime.now(timezone.utc)
        delta_7 = today - timedelta(days=7)

        self.github_client = Github(github_token)
        self.github_repo = self.github_client.get_repo(repo_name)
        self.github_repo_commits = list(self.github_repo.get_commits(until=today, since=delta_7))

        self.add_listener(self.on_ready, "on_ready")

    async def on_ready(self):
        self.__default_invite_link = (
            "https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions"
            "={scope}&scope=bot%20applications.commands"
        )
        self._get_invite_link()

    def _get_invite_link(self):
        self.no_perms_invite_link = self.__default_invite_link.format(bot_id=self.user.id, scope=0)
        self.admin_invite_link = self.__default_invite_link.format(bot_id=self.user.id, scope=8)
        self.recommended_invite_link = self.__default_invite_link.format(
            bot_id=self.user.id, scope=506850391
        )

    async def get_embed_color(self, guild_id: int):
        guild_data = await self.mongo.get_guild_data(guild_id)
        color = guild_data.configuration.embed_color
        if isinstance(color, int):
            return color
        elif isinstance(color, str):
            return int(color, 16)

    async def get_guild_bot_lang(self, guild_id):
        guild_data = await self.mongo.get_guild_data(guild_id)
        return guild_data.configuration.language

    async def async_request(self, url: str) -> dict:
        async with ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        return data

    def get_transformed_command_name(self, ctx: Union[SlashContext, MenuContext]):
        if isinstance(ctx, MenuContext):
            return ctx.name

        if not ctx.subcommand_name and not ctx.subcommand_group:
            command_name = ctx.name
        elif ctx.subcommand_name and ctx.subcommand_group:
            command_name = f"{ctx.name} {ctx.subcommand_group} {ctx.subcommand_name}"
        elif ctx.subcommand_name:
            command_name = f"{ctx.name} {ctx.subcommand_name}"
        return command_name
