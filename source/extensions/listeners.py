from core import Asteroid
from interactions import Extension, Guild
from interactions import extension_listener as listener


class Listeners(Extension):
    def __init__(self, client: Asteroid):
        # I should add type annotation since current annotation is `interactions.Client`
        self.client: Asteroid = client

    @listener
    async def on_guild_delete(self, guild: Guild):
        # TODO: Remove guild from database
        ...


def setup(client):
    Listeners(client)
