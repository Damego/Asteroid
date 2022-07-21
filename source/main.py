from os import getenv

import interactions
from core import Asteroid
from dotenv import load_dotenv
from utils.functions import load_extensions

load_dotenv()

bot = Asteroid(getenv("TOKEN"), getenv("MONGO_URL"), intents=interactions.Intents.ALL)
load_extensions(bot, "extensions")


@bot.event()
async def on_start():
    guild_data = await bot.database.get_guild(822119465575383102)
    autorole = guild_data.autoroles[0]
    print(autorole)
    autorole.content = "Go out!"
    await autorole.update()
    print(autorole)


bot.start()
