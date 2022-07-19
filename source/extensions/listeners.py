from core import Asteroid
from interactions import Extension, Guild
from interactions import extension_listener as listener


class Listeners(Extension):
    def __init__(self, client: Asteroid):
        self.client: Asteroid = (
            client  # I should add type annotation since current annotation is `Client`
        )

    @listener
    async def on_ready(self):
        print("Bot ready")

    @listener
    async def on_guild_create(self, guild: Guild):
        ...

    @listener
    async def on_guild_remove(self, guild: Guild):
        ...
