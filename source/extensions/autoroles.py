import interactions
from interactions import option  # noqa
from interactions import (  # noqa
    ActionRow,
    Button,
    ButtonStyle,
    Channel,
    Choice,
    CommandContext,
    ComponentContext,
    Extension,
    GuildMember,
    OptionType,
    Role,
    SelectMenu,
    SelectOption,
    autodefer,
)
from interactions import extension_command as command
from interactions import extension_listener as listener  # noqa

from utils import components_from_dict, get_emoji_from_str  # isort: skip
from core.client import Asteroid  # isort: skip

COLORS = {
    "Blue": ButtonStyle.PRIMARY.value,
    "Red": ButtonStyle.DANGER.value,
    "Green": ButtonStyle.SUCCESS.value,
    "Gray": ButtonStyle.SECONDARY.value,
}


class AutoRoles(Extension):
    def __init__(self, client: Asteroid):
        # I should add type annotation since current annotation is `interactions.Client`
        self.client: Asteroid = client

    @listener
    async def on_guild_member_add(self, member: GuildMember):
        guild_data = await self.client.database.get_guild(int(member.guild_id))
        for role_id in guild_data.settings.on_join_roles:
            await member.add_role(role_id, reason="[AUTOROLE ON_JOIN] Add role")

    @listener
    async def on_component(self, ctx: ComponentContext):
        if ctx.custom_id == "select_autorole" or ctx.custom_id.startswith("button_autorole"):
            roles = (
                list(map(int, ctx.data.values))
                if ctx.custom_id == "select_autorole"
                else [int(ctx.custom_id.split("|")[-1])]
            )
            code = "SELECT" if ctx.custom_id == "select_autorole" else "BUTTONS"
            for role_id in roles:
                if role_id in ctx.author.roles:
                    await ctx.author.add_role(
                        role_id, ctx.guild_id, reason=f"[AUTOROLE {code}] Add role"
                    )
                else:
                    await ctx.author.remove_role(
                        role_id, ctx.guild_id, reason=f"[AUTOROLE {code}] Remove role"
                    )

    @listener
    async def on_autocomplete(self, ctx: CommandContext):
        if ctx.data.name != "autorole":
            return
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        focused_option = [
            _option for _option in ctx.data.options[0].options[0].options if _option.focused
        ][0]
        autorole_name = [
            _option.value
            for _option in ctx.data.options[0].options[0].options
            if _option.name == "name"
        ]
        if autorole_name:
            autorole_name = autorole_name[0]
        match focused_option.name:
            case "name":
                await ctx.populate(
                    [
                        Choice(name=autorole.name, value=autorole.name)
                        for autorole in guild_data.autoroles
                    ]
                )
            case "button":
                autorole = guild_data.get_autorole(autorole_name)
                choices = []
                for action_row in autorole.component:
                    choices.extend(
                        [
                            Choice(name=button["label"], value=button["custom_id"])
                            for button in action_row["components"]
                            if focused_option.value in button["label"]
                        ]
                    )
                await ctx.populate(choices)
            case "option_name":
                autorole = guild_data.get_autorole(autorole_name)
                choices = [
                    Choice(name=option["label"], value=option["value"])
                    for option in autorole.component[0]["components"][0]["options"]
                    if focused_option.value in option["label"]
                ]
                await ctx.populate(choices)
            case "role":  # `on_join remove` command
                guild = await ctx.get_guild()
                roles = [
                    await guild.get_role(role_id) for role_id in guild_data.settings.on_join_roles
                ]
                choices = [Choice(name=role.name, value=str(role.id)) for role in roles]
                await ctx.populate(choices)

    @command(name="autorole")
    @autodefer(1, ephemeral=True)
    async def autorole(self, ctx: CommandContext):
        """Main command for all autoroles"""
        ...

    @autorole.subcommand()
    async def list(self, ctx: CommandContext):
        """Shows list of autoroles like dropdowns, button, on_joins"""
        ...

    @autorole.group()
    async def dropdown(self, ctx: CommandContext):
        """Group for dropdown autorole"""
        ...

    @dropdown.subcommand(name="create")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
    )
    @option(
        option_type=OptionType.STRING,
        name="message",
        description="The content of message",
        required=True,
    )
    @option(
        option_type=OptionType.STRING, name="placeholder", description="The dropdown placeholder"
    )
    async def dropdown_create(
        self, ctx: CommandContext, name: str, message: str, placeholder: str = None
    ):
        """Creates a dropdown autorole"""
        components = ActionRow(
            components=[
                SelectMenu(
                    custom_id="select_autorole",
                    placeholder=placeholder,
                    options=[
                        SelectOption(
                            label="None", value="None"
                        )  # We cannot send select without options
                    ],
                    disabled=True,
                )
            ]
        )
        await ctx.get_channel()
        _message = await ctx.channel.send(message, components=components)

        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        await guild_data.add_autorole(
            name=name,
            content=message,
            channel_id=int(ctx.channel_id),
            message_id=int(_message.id),
            type="select",
            component=components._json,
        )
        await ctx.send("Dropdown autorole successfully created!", ephemeral=True)

    @dropdown.subcommand(name="remove")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
        autocomplete=True,
    )
    async def dropdown_remove(self, ctx: CommandContext, name: str):
        """Removes a dropdown autorole"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        autorole = guild_data.get_autorole(name)
        if autorole is None:
            raise Exception(
                "Autorole with this name not found!"
            )  # TODO: Implement exception classes

        await guild_data.remove_autorole(autorole=autorole)

    @dropdown.subcommand(name="add-role")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
        autocomplete=True,
    )
    @option(option_type=OptionType.ROLE, name="role", description="The role to set", required=True)
    @option(
        option_type=OptionType.STRING,
        name="option_name",
        description="The name of option. Default is a role name",
    )
    @option(option_type=OptionType.STRING, name="emoji", description="The emoji for option")
    @option(
        option_type=OptionType.STRING, name="description", description="The description of option"
    )
    async def dropdown_add_role(
        self,
        ctx: CommandContext,
        name: str,
        role: Role,
        option_name: str = None,
        emoji: str = None,
        description: str = None,
    ):
        """Adds a role to dropdown"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        autorole = guild_data.get_autorole(name)
        if autorole is None:
            raise Exception(
                "Autorole with this name not found!"
            )  # TODO: Implement exception classes

        option = SelectOption(
            label=option_name or role.name,
            value=str(role.id),
            emoji=get_emoji_from_str(emoji),
            description=description,
        )
        await ctx.get_guild()
        channel: Channel = await self.client.get(
            interactions.Channel, object_id=autorole.channel_id
        )
        message = await channel.get_message(autorole.message_id)
        components = components_from_dict(message.components)
        select = components[0].components[0]
        options = select.options
        if options[0].label == "None":
            options.clear()
            select.disabled = False
        options.append(option)  # It's doesn't update json
        select.options = options  # So I need to do this thing
        await message.edit(components=components)
        autorole.component = [component._json for component in components]
        await autorole.update()

        await ctx.send("Option added", ephemeral=True)

    @dropdown.subcommand(name="remove-role")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
        autocomplete=True,
    )
    @option(
        option_type=OptionType.STRING,
        name="option_name",
        description="The option to remove",
        required=True,
        autocomplete=True,
    )
    async def dropdown_remove_role(self, ctx: CommandContext, name: str, option_name: str):
        """Removes a role of dropdown"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        autorole = guild_data.get_autorole(name)
        if autorole is None:
            raise Exception(
                "Autorole with this name not found!"
            )  # TODO: Implement exception classes
        await ctx.get_guild()
        channel: Channel = await self.client.get(
            interactions.Channel, object_id=autorole.channel_id
        )
        message = await channel.get_message(autorole.message_id)
        components = components_from_dict(message.components)
        select = components[0].components[0]
        options = select.options

        for _option in options:
            if _option.value == option_name:  # option_name is value lol
                options.remove(_option)
                break
        else:
            raise Exception("Option not found!")  # TODO: Implement exception classes

        if len(options) == 0:
            options.append(SelectOption(label="None", value="None"))
            select.disabled = True

        select.options = options
        await message.edit(components=components)
        autorole.component = [component._json for component in components]
        await autorole.update()

        await ctx.send("Option removed")

    @autorole.group()
    async def button(self, ctx: CommandContext):
        """Group for button autorole"""
        ...

    @button.subcommand(name="create")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
    )
    @option(
        option_type=OptionType.STRING,
        name="message",
        description="The content of message",
        required=True,
    )
    async def button_create(self, ctx: CommandContext, name: str, message: str):
        """Creates a button autorole"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))

        await ctx.get_channel()
        _message = await ctx.channel.send(content=message)

        await guild_data.add_autorole(
            name=name,
            content=message,
            channel_id=int(ctx.channel_id),
            message_id=int(_message.id),
            component=[],
            type="buttons",
        )
        await ctx.send("Autorole created!")

    @button.subcommand(name="remove")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
        autocomplete=True,
    )
    async def button_remove(self, ctx: CommandContext, name: str):
        """Removes a dropdown autorole"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        autorole = guild_data.get_autorole(name)
        if autorole is None:
            raise Exception(
                "Autorole with this name not found!"
            )  # TODO: Implement exception classes

        await guild_data.remove_autorole(autorole=autorole)

    @button.subcommand(name="add-role")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
        autocomplete=True,
    )
    @option(option_type=OptionType.ROLE, name="role", description="The role to set", required=True)
    @option(
        option_type=OptionType.STRING,
        name="label",
        description="The label of button. Default is a role name",
    )
    @option(option_type=OptionType.STRING, name="emoji", description="The emoji for button")
    @option(
        option_type=OptionType.INTEGER,
        name="color",
        description="The color for button. Default is Gray",
        choices=[Choice(name=name, value=value) for name, value in COLORS.items()],
    )
    async def button_add_role(
        self,
        ctx: CommandContext,
        name: str,
        role: Role,
        label: str = None,
        emoji: str = None,
        color: int = None,
    ):
        """Adds a role to button autorole"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        autorole = guild_data.get_autorole(name)
        if autorole is None:
            raise  # TODO: Implement error exception

        button = Button(
            label=label or role.name,
            custom_id=f"button_autorole|{role.id}",
            emoji=get_emoji_from_str(emoji),
            style=color if color is not None else ButtonStyle.SECONDARY,
        )

        channel: Channel = await self.client.get(
            interactions.Channel, object_id=autorole.channel_id
        )
        message = await channel.get_message(autorole.message_id)

        components = components_from_dict(message.components)
        if not components:
            components = [ActionRow(components=[button])]
        else:
            for action_row in components:
                if len(action_row.components) < 5:
                    _components = action_row.components  # I need to update ._json
                    _components.append(
                        button
                    )  # Simply action_row.components.append(button) does not update ._json
                    action_row.components = _components  # So I can only wait fix
                    break
            else:
                if len(components) < 5:
                    components.append(ActionRow(components=[button]))
                else:
                    raise Exception("Buttons limit")  # TODO: Exception classes
        autorole.component = [_._json for _ in components]
        print(autorole.component)
        await autorole.update()
        await message.edit(components=components)

        await ctx.send("Button added!")

    @button.subcommand(name="remove-role")
    @option(
        option_type=OptionType.STRING,
        name="name",
        description="The name of autorole",
        required=True,
        autocomplete=True,
    )
    @option(
        option_type=OptionType.STRING,
        name="button",
        description="The button to remove",
        required=True,
        autocomplete=True,
    )
    async def button_remove_role(self, ctx: CommandContext, name: str, button: str):
        """Removes a role of button autorole"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        autorole = guild_data.get_autorole(name)
        if autorole is None:
            raise  # TODO: Implement error exception

        channel: Channel = await self.client.get(
            interactions.Channel, object_id=autorole.channel_id
        )
        message = await channel.get_message(autorole.message_id)
        components = components_from_dict(message.components)
        if not components:
            raise Exception("No buttons lol")

        _break = False
        for action_row in components:
            for _button in action_row.components:
                if _button.custom_id == button:
                    _components = action_row.components  # I need to update ._json
                    _components.remove(
                        _button
                    )  # Simply action_row.components.append(button) does not update ._json
                    action_row.components = _components  # So I can only wait fix
                    _break = True
            if _break:
                break
        else:
            raise Exception("Button not found")
        await message.edit(components=components)
        autorole.component = [_._json for _ in components]
        await autorole.update()

        await ctx.send("Button removed!")

    @autorole.group(name="on_joina")
    async def on_join(self, ctx: CommandContext):
        """Group for on_join roles"""
        ...

    @on_join.subcommand(name="add")
    @option(option_type=OptionType.ROLE, name="role", description="The role to add", required=True)
    async def on_join_add(self, ctx: CommandContext, role: Role):
        """Adds a role"""
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        role_id = int(role.id)
        roles = guild_data.settings.on_join_roles
        if role_id in roles:
            raise Exception("Role already exist")

        guild_data.settings.on_join_roles.append(role_id)
        await guild_data.settings.update()
        await ctx.send("Role added")

    @on_join.subcommand(name="remove")
    @option(
        option_type=OptionType.STRING,  # Not int because snowflake is too long.
        name="role",
        description="The role to remove",
        required=True,
        autocomplete=True,
    )
    async def on_join_remove(self, ctx: CommandContext, role: str):
        """Removes a role"""
        await ctx.defer()
        role_id = int(role)
        guild_data = await self.client.database.get_guild(int(ctx.guild_id))
        if role_id not in guild_data.settings.on_join_roles:
            raise Exception("Role not in list")  # TODO: Exception class

        guild_data.settings.on_join_roles.remove(role_id)
        await guild_data.settings.update()
        await ctx.send("Role removed")


def setup(client):
    AutoRoles(client)
