from typing import List
from discord.ext.commands import Cog as _Cog


class Cog(_Cog):
    name: str = None
    hidden: bool = False
    description: str = None
    emoji: str = '❓'
    private_guild_id: List[int] = None