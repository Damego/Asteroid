from asyncio import TimeoutError
from discord_components import Button, ButtonStyle
from discord_slash_components_bridge import ComponentContext

async def get_interaction(bot, ctx, message) -> ComponentContext:
    try:
        return await bot.wait_for(
            'button_click',
            check=lambda i: i.user.id == ctx.author.id and i.message.id == message.id,
            timeout=120)
    except TimeoutError:
        await message.edit(components=[])
        return
    except Exception as e:
        print('error', e)



class PaginatorStyle:
    def style1(pages:int):
        return [
            [
                Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
                Button(style=ButtonStyle.green, label=f'{1}/{pages}', emoji='🏠', id='home', disabled=True),
                Button(style=ButtonStyle.gray, label='→', id='next'),
            ]
        ]

    def style2(pages:int):
        return [
            [
                Button(style=ButtonStyle.gray, label='<<', id='first', disabled=True),
                Button(style=ButtonStyle.gray, label='←', id='back', disabled=True),
                Button(style=ButtonStyle.blue, label=f'{1}/{pages}', disabled=True),
                Button(style=ButtonStyle.gray, label='→', id='next'),
                Button(style=ButtonStyle.gray, label='>>', id='last')
            ]
        ]


class PaginatorCheckButtonID:
    def __init__(self, components:list, pages:int) -> None:
        self.components = components
        self.pages = pages


    def _style1(self, button_id:int, page:int):
        if button_id == 'back':
            if page == self.pages:
                self.components[0][-1].disabled = False
            page -= 1
            if page == 1:
                self.components[0][0].disabled = True
                self.components[0][1].disabled = True
            elif page == 2:
                self.components[0][0].disabled = False
        elif button_id == 'next':
            if page == 1:
                self.components[0][0].disabled = False
                self.components[0][1].disabled = False
            page += 1
            if page == self.pages:
                self.components[0][-1].disabled = True
            elif page == self.pages-1:
                self.components[0][-1].disabled = False
        elif button_id == 'home':
            page = 1
            self.components[0][0].disabled = True
            self.components[0][1].disabled = True

        self.components[0][1].label = f'{page}/{self.pages}'
        return page

    def _style2(self, button_id:int, page:int):
        first_button = self.components[0][0]
        second_button = self.components[0][1]
        second_last_button = self.components[0][-2]
        last_button = self.components[0][-1]
        pages_button = self.components[0][2]
        if button_id == 'back':
            if page == self.pages:
                second_last_button.disabled = False
                last_button.disabled = False
            page -= 1
            if page == 1:
                first_button.disabled = True
                second_button.disabled = True
            elif page == 2:
                first_button.disabled = False
                second_button.disabled = False

        elif button_id == 'first':
            page = 1
            first_button.disabled = True
            second_button.disabled = True
            second_last_button.disabled = False
            last_button.disabled = False

        elif button_id == 'last':
            page = self.pages
            first_button.disabled = False
            second_button.disabled = False
            second_last_button.disabled = True
            last_button.disabled = True

        elif button_id == 'next':
            if page == 1:
                first_button.disabled = False
                second_button.disabled = False
            page += 1
            if page == self.pages:
                second_last_button.disabled = True
                last_button.disabled = True
            elif page == self.pages-1:
                second_last_button.disabled = False
                last_button.disabled = False
        pages_button.label = f'{page}/{self.pages}'

        return page
