import interactions

from core import Asteroid
from core.context import CommandContext


class TestCog(interactions.Extension):
    def __init__(self, client):
        self.client: Asteroid = client

    @interactions.extension_command()
    async def cursed(self, ctx: CommandContext):
        embeds = [interactions.Embed(title=f"Embed {i}") for i in range(1, 6)]
        components = [
            interactions.Button(label=f"Button {i}", style=1, custom_id=f"{i}") for i in range(1, 6)
        ]
        await (ctx << "cursed message" << embeds << components << {"ephemeral": True})


def setup(bot):
    TestCog(bot)
