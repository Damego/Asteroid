from os import listdir
from typing import Union

from aiohttp import ClientSession, ClientResponse
from discord.ext.commands import Bot
from discord_slash import SlashContext, MenuContext
from discord_slash_components_bridge import SlashCommand

from my_utils.mongo import Mongo


class AsteroidBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__default_invite_link = None
        self.mongo = Mongo()
        self.slash = SlashCommand(self, sync_commands=False, sync_on_cog_reload=False)

        self.add_listener(self.on_ready, 'on_ready')
        self._load_extensions()

    async def on_ready(self):
        self.__default_invite_link = 'https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions' \
                                     '={scope}&scope=bot%20applications.commands'
        self._get_invite_link()

    def _get_invite_link(self):
        self.no_perms_invite_link = self.__default_invite_link.format(bot_id=self.user.id, scope=0)
        self.admin_invite_link = self.__default_invite_link.format(bot_id=self.user.id, scope=8)
        self.recommended_invite_link = self.__default_invite_link.format(bot_id=self.user.id, scope=506850391)

    def _load_extensions(self):
        for filename in listdir('./cogs'):
            if filename.startswith('_'):
                continue
            if filename.endswith('.py'):
                self.load_extension(f'cogs.{filename[:-3]}')
            elif '.' in filename:
                continue
            else:
                self.load_extension(f'cogs.{filename}')

    def get_guild_main_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['configuration']

    def get_guild_users_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['users']

    def get_guild_tags_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['tags']

    def get_guild_voice_time_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['voice_time']

    def get_guild_reaction_roles_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['reaction_roles']

    def get_guild_giveaways_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['giveaways']

    def get_guild_auto_role_collection(self, guild_id:int):
        return self.mongo.connection[str(guild_id)]['auto_role']

    def get_guild_cogs_collection(self, guild_id: int):
        return self.mongo.connection[str(guild_id)]['cogs_config']

    def _extract_from_guild_collection(self, guild_id: int, key: str):
        collection = self.get_guild_main_collection(guild_id)
        value = collection.find_one({'_id': 'configuration'}).get(key)
        if value is not None:
            return value

        if key == 'embed_color':
            value = '0x000001'
        elif key == 'lang':
            value = 'en'
        else:
            value = None
        return value

    def get_embed_color(self, guild_id):
        color = self._extract_from_guild_collection(guild_id, 'embed_color')
        return int(color, 16)

    def get_guild_bot_lang(self, guild_id):
        return self._extract_from_guild_collection(guild_id, 'lang')

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
