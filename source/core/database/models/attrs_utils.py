from functools import wraps
from typing import TYPE_CHECKING, Callable

import attrs

if TYPE_CHECKING:
    from ..client import DataBaseClient


class MISSING:
    ...


@attrs.define(eq=False, init=False)
class DictSerializerMixin:
    _json: dict = attrs.field(init=False, repr=False)

    def __init__(self, kwargs_dict: dict = None, **other_kwargs):
        kwargs = kwargs_dict or other_kwargs
        self._json = kwargs.copy()
        database = kwargs.pop("_database", None)
        passed_kwargs = {}
        attribs: tuple[attrs.Attribute, ...] = self.__attrs_attrs__

        for attrib in attribs:
            if not attrib.init:
                continue
            metadata = attrib.metadata
            attr_name = attrib.name
            if (value := kwargs.get(metadata["alias"], MISSING)) is MISSING:
                if (value := kwargs.get(attr_name, MISSING)) is MISSING:
                    value = MISSING

            if value is not None and value is not MISSING:
                if isinstance(value, list):
                    for item in value:
                        if metadata["add_database"]:
                            item["_database"] = database
                        elif metadata["add_guild_id"]:
                            item["guild_id"] = kwargs.get("guild_id", MISSING)
                elif isinstance(value, dict):
                    if metadata["add_database"]:
                        value["_database"] = database
                    elif metadata["add_guild_id"]:
                        value["guild_id"] = kwargs.get("guild_id", MISSING)

            passed_kwargs[attr_name] = value
        print(passed_kwargs)
        self.__attrs_init__(**passed_kwargs)


@attrs.define(eq=False, init=False)
class DataBaseSerializerMixin(DictSerializerMixin):
    _database: "DataBaseClient" = attrs.field(init=False, repr=False)

    def __init__(self, kwargs_dict: dict = None, **other_kwargs):
        kwargs = kwargs_dict or other_kwargs
        self._database = kwargs.get("_database", None)
        super().__init__(**kwargs)

    async def update(self):
        _json = attrs.asdict(self)
        data = {key: value for key, value in _json.items() if self._json[key] != value}

        match str(self.__class__.__name__):
            case "GuildUser":
                await self._database.update_user(self._json["id"], self._json["guild_id"], data)


def convert_list(obj: Callable):
    def wrapper(list_data: list):
        return [obj(**data) for data in list_data]

    return wrapper


define_defaults = dict(kw_only=True, eq=False, init=False)


@wraps(attrs.define)
def define(**kwargs):
    return attrs.define(**kwargs, **define_defaults)


@wraps(attrs.field)
def field(
    converter=None,
    default=attrs.NOTHING,
    add_database: bool = False,
    add_guild_id: bool = False,
    alias: str = None,
    **kwargs,
):
    metadata = dict(add_database=add_database, alias=alias, add_guild_id=add_guild_id)

    return attrs.field(converter=converter, default=default, metadata=metadata, **kwargs)
