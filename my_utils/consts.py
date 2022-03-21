from enum import IntEnum


class DiscordColors(IntEnum):
    BLURPLE = 0x5865F2
    GREEN = 0x57F287
    YELLOW = 0xFEE75C
    FUCHSIA = 0xEB459E
    RED = 0xED4245
    WHITE = 0xFFFFFF
    BLACK = 0x000000


class SystemChannels(IntEnum):
    ERRORS_CHANNEL = 863001051523055626
    COMMANDS_USING = 933755239583080448
    ISSUES_REPORT = 955413641551818752
    SERVERS_UPDATE = 903920844114362389
    BOT_UPTIME = 891222610166284368


__version__ = "2"

test_guild_id = [829333896561819648]
discord_components_guild_id = [
    847283544803508254,
    422989643634442240,
]  # Second is for testing
test_global_guilds_ids = [422989643634442240, 822119465575383102]
all_guild_ids = [847283544803508254, 422989643634442240, 822119465575383102]
LANGUAGES_LIST = ["Russian", "English"]

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
