from os import getenv, environ
from dotenv import load_dotenv
from pymongo import MongoClient
from discord_components import ComponentsBot

class MongoComponentsBot(ComponentsBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mongodatabase = self.get_database()
        self.add_callback = self.components_manager.add_callback

    def get_database(self):
        load_dotenv()
        return MongoClient(getenv('MONGODB_URL'))['guilds']

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

    def get_guild_select_role_collection(self, guild_id:int):
        return self.get_guild_main_collection(guild_id)['select_role']

    def get_embed_color(self, guild_id):
        collection = self.get_guild_configuration_collection(guild_id)
        color = collection.find_one({'_id':'configuration'})['embed_color']
        return int(color, 16)

    def get_guild_prefix(self, guild_id):
        collection = self.get_guild_configuration_collection(guild_id)
        prefix = collection.find_one({'_id':'configuration'})['prefix']
        return prefix
