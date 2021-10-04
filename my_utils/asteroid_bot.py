from os import getenv

from dotenv import load_dotenv
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext.commands import Bot
import certifi



class AsteroidBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongodatabase = self.get_database()

    def get_database(self):
        load_dotenv()
        return MongoClient(getenv('MONGODB_URL'), tlsCAFile=certifi.where())['guilds']

    def get_guild_main_collection(self, guild_id:int):
        return self.mongodatabase[str(guild_id)]

    def get_guild_configuration_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['configuration']

    def get_guild_users_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['users']

    def get_guild_tags_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['tags']

    def get_guild_voice_time_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['voice_time']

    def get_guild_level_roles_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['roles_by_level']

    def get_guild_reaction_roles_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['reaction_roles']

    def get_guild_giveaways_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['giveaways']

    def get_guild_auto_role_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['auto_role']

    def get_guild_cogs_collection(self, guild_id: int):
        return self.get_guild_main_collection(guild_id)['cogs_config']

    def _extract_from_guild_collection(self, guild_id: int, key: str):
        collection = self.get_guild_configuration_collection(guild_id)
        value = collection.find_one({'_id':'configuration'}).get(key)
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