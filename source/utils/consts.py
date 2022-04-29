from enum import IntEnum


class DiscordColors(IntEnum):
    BLURPLE = 0x5865F2
    GREEN = 0x57F287
    YELLOW = 0xFEE75C
    FUCHSIA = 0xEB459E
    RED = 0xED4245
    WHITE = 0xFFFFFF
    BLACK = 0x000000
    EMBED_COLOR = 0x2F3136


class SystemChannels(IntEnum):
    ERRORS_CHANNEL = 863001051523055626
    COMMANDS_USING_CHANNEL = 933755239583080448
    ISSUES_REPORT_CHANNEL = 955413641551818752
    SERVERS_UPDATE_CHANNEL = 903920844114362389
    BOT_UPTIME_CHANNEL = 891222610166284368
    GENSHIN_DAILY_REWARDS = 955461010435756074
    MANGAS_UPDATES = 969464310294278214


__version__ = "2"

test_guild_id = [829333896561819648]
test_global_guilds_ids = [422989643634442240, 822119465575383102]

owner_ids = [143773579320754177]
author = "Damego"

github_link = "https://github.com/Damego"

multiplier = {
    "д": 86400,
    "ч": 3600,
    "м": 60,
    "с": 1,
    "d": 86400,
    "h": 3600,
    "m": 60,
    "s": 1,
}

PUBLIC_EXTENSIONS = [
    "Fun",
    "Levels",
    "AutoRole",
    "Genshin",
    "Misc",
    "Moderation",
    "Music",
    "PrivateRooms",
    "StarBoard",
    "Tags",
    "Utilities",
]
