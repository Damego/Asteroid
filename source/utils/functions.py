def transform_permission(permission: str):
    return permission.replace("_", " ").replace("guild", "server").title()


def format_voice_time(voice_time: int, content: dict):
    days = (voice_time // 60) // 24
    hours = (voice_time // 60) % 24
    minutes = voice_time % 60
    formatted = ""
    if days != 0:
        formatted += f" {days} {content['DAYS']}"
    if hours != 0:
        formatted += f" {hours} {content['HOURS']}"
    if minutes != 0:
        formatted += f" {minutes} {content['MINUTES']}"
    return formatted.strip() if formatted else None
