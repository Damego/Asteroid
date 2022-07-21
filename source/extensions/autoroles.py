from core.client import Asteroid
from interactions import ButtonStyle, Choice, CommandContext, Extension, OptionType, Role
from interactions import extension_command as command
from interactions import extension_listener as listener  # noqa
from interactions import option

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

    @command()
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
    @option(str, name="name", description="The name of autorole", required=True)
    @option(str, name="message", description="The content of message", required=True)
    @option(str, name="placeholder", description="The dropdown placeholder")
    async def dropdown_create(
        self, ctx: CommandContext, name: str, message: str, placeholder: str = None
    ):
        """Creates a dropdown autorole"""
        ...

    @dropdown.subcommand(name="remove")
    @option(str, name="name", description="The name of autorole", required=True, autocomplete=True)
    async def dropdown_remove(self, ctx: CommandContext, name: str):
        """Removes a dropdown autorole"""
        ...

    @dropdown.subcommand(name="add-role")
    @option(str, name="name", description="The name of autorole", required=True, autocomplete=True)
    @option(OptionType.ROLE, name="role", description="The role to set", required=True)
    @option(str, name="option-name", description="The name of option. Default is a role name")
    @option(str, name="emoji", description="The emoji for option")
    @option(str, name="description", description="The description of option")
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
        ...

    @dropdown.subcommand(name="remove-role")
    @option(str, name="name", description="The name of autorole", required=True, autocomplete=True)
    async def dropdown_remove_role(self, ctx: CommandContext, name: str):
        """Removes a role of dropdown"""

        ...

    @autorole.group()
    async def button(self, ctx: CommandContext):
        """Group for button autorole"""
        ...

    @button.subcommand(name="create")
    @option(str, name="name", description="The name of autorole", required=True)
    @option(str, name="message", description="The content of message", required=True)
    async def button_create(self, ctx: CommandContext, name: str, message: str):
        """Creates a button autorole"""
        ...

    @button.subcommand(name="remove")
    @option(str, name="name", description="The name of autorole", required=True, autocomplete=True)
    async def button_remove(self, ctx: CommandContext, name: str):
        """Removes a dropdown autorole"""
        ...

    @button.subcommand(name="add-role")
    @option(str, name="name", description="The name of autorole", required=True, autocomplete=True)
    @option(OptionType.ROLE, name="role", description="The role to set", required=True)
    @option(str, name="label", description="The label of button. Default is a role name")
    @option(str, name="emoji", description="The emoji for button")
    @option(
        int,
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
        ...

    @button.subcommand(name="remove-role")
    @option(str, name="name", description="The name of autorole", required=True, autocomplete=True)
    async def button_remove_role(self, ctx: CommandContext, name: str):
        """Removes a role of button autorole"""
        ...

    @autorole.group()
    async def on_join(self, ctx: CommandContext):
        """Group for on_join roles"""
        ...

    @on_join.subcommand("add")
    @option(OptionType.ROLE, name="role", description="The role to add", required=True)
    async def on_join_add(self, ctx: CommandContext, role: Role):
        """Adds a role"""
        ...

    @on_join.subcommand("remove")
    @option(int, name="role", description="The role to remove", required=True, autocomplete=True)
    async def on_join_remove(self, ctx: CommandContext, role: int):
        """Removes a role"""
        ...


def setup(client):
    AutoRoles(client)
