from os import getenv

import certifi
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()


class Mongo:
    def __init__(self) -> None:
        self._connection = MongoClient(getenv('MONGODB_URL'), tlsCAFile=certifi.where())['guilds']

    def add_guild(self, guild_id: int):
        ...

    def add_user(self, guild_id: int, user_id: int):
        ...

    def update_user(self, guild_id: int, user_id: int, update_type: str, data: dict):
        """
        ## Parameters
        - guild_id: int -- ID of server
        - user_id: int -- ID of user
        - update_type: str -- type of update ('$set', '$inc', etc.)
        - data: dict -- data for update
        """

        collection = self._connection[str(guild_id)]['users']
        collection.update_one(
            {'_id': str(user_id)},
            {update_type: data},
            upsert=True
        )

    def get_user_data(self, guild_id: int, user_id: int) -> dict:
        collection = self._connection[str(guild_id)]['users']
        return collection.find_one({'_id': str(user_id)})

    def remove_user(self, guild_id: int, user_id: int):
        ...

    @property
    def connection(self):
        return self._connection
    