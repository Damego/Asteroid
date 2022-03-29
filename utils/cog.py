from typing import List, Union
from discord.ext.commands import Cog as _Cog


class Cog(_Cog):
    name: str = None
    hidden: bool = False
    description: str = None
    emoji: Union[str, int] = "❓"
    private_guild_id: List[int] = None
