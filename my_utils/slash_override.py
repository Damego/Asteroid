from discord_slash import SlashCommand, model, error


def _get_cog_slash_commands(self, cog, func_list):
    res = [
        x
        for x in func_list
        if isinstance(x, (model.CogBaseCommandObject, model.CogSubcommandObject))
    ]

    for x in res:
        x.cog = cog
        if isinstance(x, model.CogBaseCommandObject):
            if x.name in self.commands:
                raise error.DuplicateCommand(x.name)
            self.commands[x.name] = x
        else:
            if x.base in self.commands:
                base_command = self.commands[x.base]
                for i in x.allowed_guild_ids:
                    if i not in base_command.allowed_guild_ids:
                        base_command.allowed_guild_ids.append(i)

                base_permissions = x.base_command_data["api_permissions"]
                if base_permissions:
                    for applicable_guild in base_permissions:
                        if applicable_guild not in base_command.permissions:
                            base_command.permissions[applicable_guild] = []
                        base_command.permissions[applicable_guild].extend(
                            base_permissions[applicable_guild]
                        )

                self.commands[x.base].has_subcommands = True

            else:
                self.commands[x.base] = model.CogBaseCommandObject(x.base, x.base_command_data)
                self.commands[x.base].cog = cog
            if x.base not in self.subcommands:
                self.subcommands[x.base] = {}
            if x.subcommand_group:
                if x.subcommand_group not in self.subcommands[x.base]:
                    self.subcommands[x.base][x.subcommand_group] = {}
                if x.name in self.subcommands[x.base][x.subcommand_group]:
                    raise error.DuplicateCommand(f"{x.base} {x.subcommand_group} {x.name}")
                self.subcommands[x.base][x.subcommand_group][x.name] = x
            else:
                if x.name in self.subcommands[x.base]:
                    raise error.DuplicateCommand(f"{x.base} {x.name}")
                self.subcommands[x.base][x.name] = x

SlashCommand._get_cog_slash_commands = _get_cog_slash_commands