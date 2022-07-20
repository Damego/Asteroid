from interactions import Client

from .database import DataBaseClient

__all__ = ["Asteroid"]


class Asteroid(Client):
    def __init__(self, bot_token: str, mongodb_url: str, **kwargs):
        super().__init__(bot_token, **kwargs)
        self.database = DataBaseClient(mongodb_url)
