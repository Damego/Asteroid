from interactions import Client, get

from .database import DataBaseClient

__all__ = ["Asteroid"]


class Asteroid(Client):
    def __init__(self, bot_token: str, mongodb_url: str, **kwargs):
        super().__init__(bot_token, **kwargs)
        self.database = DataBaseClient(mongodb_url)

    async def get(self, *args, **kwargs):
        return await get(self, *args, **kwargs)
