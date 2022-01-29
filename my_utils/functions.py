def transform_permission(permission: str):
    return permission.replace("_", " ").replace("guild", "server").title()
