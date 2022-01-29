"""
MIT License

Copyright (c) 2021 Polsulpicien

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

##############################################
#       Made by Polsulpicien#5020            #
#                                            #
# DON'T CHANGE THE FOOTER TEXT OF THE EMBEDS #
##############################################


from asyncio import TimeoutError
from math import pi, tau, e, sqrt

from discord import Embed, Member
from discord_components import Button, ButtonStyle
from discord_slash import SlashContext
from discord_slash_components_bridge import ComponentContext, ComponentMessage

from my_utils import AsteroidBot


def calculate(expression: str):
    result = ""
    expression = expression.replace("×", "*")
    expression = expression.replace("÷", "/")
    expression = expression.replace("^2", "**2")
    expression = expression.replace("^3", "**3")
    expression = expression.replace("^", "**")
    expression = expression.replace("√", "sqrt")

    try:
        result = eval(expression, {"sqrt": sqrt})
    except:
        result = "Syntax Error!\nDon't forget the sign(s) ('×', '÷', ...).\nnot: 3(9+1) but 3×(9+1)"

    return result


def input_formatter(original: str, new: str):
    if "Syntax Error!" in original:
        original = "|"
    lst = list(original)
    try:
        index = lst.index("|")
        lst.remove("|")
    except:
        index = 0

    if new == "×":
        i = index - 1
        try:
            if lst[i] == "×":
                lst.insert(index + 1, "|")
                original = "".join(lst)
                return original
        except:
            lst.insert(index + 1, "|")
            original = "".join(lst)
            return original
        try:
            if lst[index] == "×":
                lst.insert(index, "|")
                original = "".join(lst)
                return original
            else:
                lst.insert(index, "×")
        except:
            lst.insert(index, "×")
    elif new == "√":
        lst.insert(index, "√()")
    elif new in "X²X³Xˣ":
        if "^" not in lst:
            if new == "X²":
                lst.insert(index, "^2")
            elif new == "X³":
                lst.insert(index, "^3")
            elif new == "Xˣ":
                lst.insert(index, "^")
    else:
        lst.insert(index, new)

    lst.insert(index + 1, "|")
    original = "".join(lst)
    return original


class Calculator:
    def __init__(self, bot: AsteroidBot):
        self.bot = bot
        self.normal_components = [
            [
                Button(style=ButtonStyle.grey, label="1", id="1"),
                Button(style=ButtonStyle.grey, label="2", id="2"),
                Button(style=ButtonStyle.grey, label="3", id="3"),
                Button(style=ButtonStyle.blue, label="×", id="*"),
                Button(style=ButtonStyle.red, label="Exit", id="Exit"),
            ],
            [
                Button(style=ButtonStyle.grey, label="4", id="4"),
                Button(style=ButtonStyle.grey, label="5", id="5"),
                Button(style=ButtonStyle.grey, label="6", id="6"),
                Button(style=ButtonStyle.blue, label="÷", id="/"),
                Button(style=ButtonStyle.red, label="⌫", id="⌫"),
            ],
            [
                Button(style=ButtonStyle.grey, label="7", id="7"),
                Button(style=ButtonStyle.grey, label="8", id="8"),
                Button(style=ButtonStyle.grey, label="9", id="9"),
                Button(style=ButtonStyle.blue, label="+", id="+"),
                Button(style=ButtonStyle.red, label="Clear", id="Clear"),
            ],
            [
                Button(style=ButtonStyle.grey, label="00", id="00"),
                Button(style=ButtonStyle.grey, label="0", id="0"),
                Button(style=ButtonStyle.grey, label=".", id="."),
                Button(style=ButtonStyle.blue, label="-", id="-"),
                Button(style=ButtonStyle.green, label="=", id="="),
            ],
            [
                Button(style=ButtonStyle.green, label="❮", id="❮"),
                Button(style=ButtonStyle.green, label="❯", id="❯"),
                Button(
                    style=ButtonStyle.grey,
                    label="Change to scientific mode",
                    emoji="\U0001f9d1\u200D\U0001f52c",
                    id="scientific_mode",
                ),
            ],
        ]

        self.scientific_components = [
            [
                Button(style=ButtonStyle.grey, label="(", id="("),
                Button(style=ButtonStyle.grey, label=")", id=")"),
                Button(style=ButtonStyle.grey, label="π", id=str(pi)),
                Button(style=ButtonStyle.blue, label="×", id="*"),
                Button(style=ButtonStyle.red, label="Exit", id="Exit"),
            ],
            [
                Button(style=ButtonStyle.grey, label="X²", disabled=True),
                Button(style=ButtonStyle.grey, label="X³", disabled=True),
                Button(style=ButtonStyle.grey, label="Xˣ", disabled=True),
                Button(style=ButtonStyle.blue, label="÷", id="/"),
                Button(style=ButtonStyle.red, label="⌫", id="⌫"),
            ],
            [
                Button(style=ButtonStyle.grey, label="e", id=str(e)),
                Button(style=ButtonStyle.grey, label="τ", id=str(tau)),
                Button(style=ButtonStyle.grey, label="000", id="000"),
                Button(style=ButtonStyle.blue, label="+", id="+"),
                Button(style=ButtonStyle.red, label="Clear", id="Clear"),
            ],
            [
                Button(style=ButtonStyle.grey, label="√", id="√"),
                Button(style=ButtonStyle.grey, label=" ", disabled=True),
                Button(style=ButtonStyle.grey, label=" ", disabled=True),
                Button(style=ButtonStyle.blue, label="-", id="-"),
                Button(style=ButtonStyle.green, label="=", id="="),
            ],
            [
                Button(style=ButtonStyle.green, label="❮", id="❮"),
                Button(style=ButtonStyle.green, label="❯", id="❯"),
                Button(
                    style=ButtonStyle.grey,
                    label="Change to normal modeㅤ",
                    emoji="\U0001f468\u200D\U0001f3eb",
                    id="normal_mode",
                ),
            ],
        ]

    def _get_embed(self, author: Member, embed_description: str):
        embed = Embed(
            title=f"{author}'s calculator",
            description=embed_description,
            color=0x2F3136,
        )
        embed.set_footer(text="https://github.com/Polsulpicien")
        return embed

    async def start(self, ctx: SlashContext):
        affichage = "|"
        is_normal_mode = True
        embed = self._get_embed(ctx.author, f"```{affichage}```")
        expression = ""
        message: ComponentMessage = await ctx.send(
            components=self.normal_components, embed=embed
        )

        while True:
            try:
                interaction: ComponentContext = await self.bot.wait_for(
                    "button_click",
                    check=lambda inter: inter.author.id == ctx.author.id
                    and inter.message.id == message.id,
                    timeout=60,
                )
            except TimeoutError:
                return await message.edit(
                    embed=self._get_embed(ctx.author, f"```{affichage}```"),
                    components=[
                        row.disable_components()
                        for row in interaction.message.components
                    ],
                )

            if interaction.custom_id == "Exit":
                embed = self._get_embed(
                    ctx.author, interaction.message.embeds[0].description
                )
                return await interaction.edit_origin(
                    embed=embed,
                    components=[
                        row.disable_components()
                        for row in interaction.message.components
                    ],
                )
            elif interaction.custom_id == "⌫":
                lst = list(interaction.message.embeds[0].description.replace("`", ""))
                if len(lst) > 1:
                    try:
                        index = lst.index("|")
                        x = index - 2
                        y = index + 1
                        if lst[x] == "×" and lst[y] == "×":
                            lst.pop(index - 1)
                            lst.pop(index - 2)
                        else:
                            lst.pop(index - 1)
                    except:
                        lst = ["|"]
                affichage = "".join(lst)
                expression = affichage
            elif interaction.custom_id == "Clear":
                expression = ""
                affichage = "|"
            elif interaction.custom_id == "=":
                if "Syntax Error!" in affichage or affichage == "|":
                    affichage = "|"
                else:
                    expression = expression.replace("|", "")
                    expression = calculate(expression)
                    affichage = f"{affichage.replace('|','')}={expression}"
                expression = ""
            elif interaction.custom_id == "❮":
                lst = list(interaction.message.embeds[0].description.replace("`", ""))
                if len(lst) > 1:
                    try:
                        index = lst.index("|")
                        lst.remove("|")
                        lst.insert(index - 1, "|")
                    except:
                        lst = ["|"]
                affichage = "".join(lst)
            elif interaction.custom_id == "❯":
                lst = list(interaction.message.embeds[0].description.replace("`", ""))
                if len(lst) > 1:
                    try:
                        index = lst.index("|")
                        lst.remove("|")
                        lst.insert(index + 1, "|")
                    except:
                        lst = ["|"]
                affichage = "".join(lst)
            elif interaction.custom_id == "scientific_mode":
                is_normal_mode = False
                await interaction.edit_origin(
                    embed=self._get_embed(ctx.author, f"```{affichage}```"),
                    components=self.scientific_components,
                )
            elif interaction.custom_id == "normal_mode":
                is_normal_mode = True
                await interaction.edit_origin(
                    embed=self._get_embed(ctx.author, f"```{affichage}```"),
                    components=self.normal_components,
                )
            else:
                if "=" in affichage:
                    affichage = ""
                expression = input_formatter(
                    original=affichage, new=interaction.component.label
                )
                affichage = expression

            if interaction.custom_id not in ["scientific_mode", "normal_mode"]:
                if is_normal_mode:
                    await interaction.edit_origin(
                        embed=self._get_embed(ctx.author, f"```{affichage}```"),
                        components=self.normal_components,
                    )
                else:
                    await interaction.edit_origin(
                        embed=self._get_embed(ctx.author, f"```{affichage}```"),
                        components=self.scientific_components,
                    )


def setup(bot):
    bot.add_cog(Calculator(bot))
