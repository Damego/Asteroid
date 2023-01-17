from os import getenv

from dotenv import load_dotenv
from interactions import Intents
from interactions.ext.i18n import setup

from core import Asteroid
from utils.functions import load_extensions

load_dotenv()

client = Asteroid(
    getenv("MONGO_URL"),
    intents=Intents.ALL,
)
i18n = setup(client)

load_extensions(client, "extensions")


@client.event
async def on_ready():
    print("Bot ready")


client.start(getenv("TOKEN"))
