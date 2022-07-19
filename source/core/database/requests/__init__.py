from interactions import Client

__all__ = []


class Asteroid(Client):
    def __init__(self, bot_token: str, mongodb_url: str, **kwargs):
        super().__init__(bot_token, **kwargs)
