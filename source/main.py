from os import getenv

import interactions
from dotenv import load_dotenv

from core import Asteroid
from utils.functions import load_extensions

load_dotenv()

client = Asteroid(getenv("TOKEN"), getenv("MONGO_URL"), intents=interactions.Intents.ALL)
load_extensions(client, "extensions")


@client.event
async def on_ready():
    print("Bot ready")


client.start()
