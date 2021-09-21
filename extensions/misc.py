import json
from os import remove, environ
from random import randint
from asyncio import sleep

import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle
from discord_components.interaction import Interaction
import qrcode
import requests

from .bot_settings import (
    DurationConverter,
    multiplier,
    version,
    is_administrator_or_bot_owner,
    )
from ._hltv import HLTV


class Misc(commands.Cog, description='Misc commands'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.emoji = '💡'


    @commands.command(name='random', description='Send random name', help='[from] [to]')
    async def random_num(self, ctx, arg1:int, arg2:int):
        random_number = randint(arg1, arg2)
        await ctx.reply(f'Random num is {random_number}')


    @commands.group(
        name='info',
        description='Show information about server member',
        help='(user)',
        invoke_without_command=True)
    async def info(self, ctx:commands.Context, member:discord.Member=None):
        if not member:
            member = ctx.author

        embed = discord.Embed(title=f'Информация о пользователе {member}', color=self.bot.get_embed_color(ctx.guild.id))
        embed.set_thumbnail(url=member.avatar_url)

        member_roles = [role.mention for role in member.roles if role.name != "@everyone"][::-1]

        member_roles = ', '.join(member_roles)

        member_status = str(member.status)
        status = {
            'online':'<:s_online:850792217031082051> Online',
            'dnd':'<:dnd:850792216943525936> Do not disturb',
            'idle':'<:s_afk:850792216732368937> Idle',
            'offline':'<:s_offline:850792217262030969> Offline'
        }

        embed.add_field(name="Main information:", value=f"""
            **Date of registration in Discord:** <t:{int(member.created_at.timestamp())}:F>
            **Date of joined on server:** <t:{int(member.joined_at.timestamp())}:F>
            **Current status:** {status.get(member_status)}
            **Roles:** {member_roles}
            """, inline=False)

        await ctx.send(embed=embed)


    @info.command(name='server',
    description='Show information about server',
    help='')
    async def server_info(self, ctx:commands.Context):
        guild = ctx.guild
        embed = discord.Embed(title=f'Information about {guild.name}', color=self.bot.get_embed_color(guild.id))
        embed.add_field(name='Creation date:', value=f'<t:{int(guild.created_at.timestamp())}:F>', inline=False)
        embed.add_field(name='Server owner:', value=guild.owner.mention, inline=False)

        embed.add_field(name='Quantity',
            value=f"""
                :man_standing: **Members:** {guild.member_count}
                :crown: **Roles:** {len(guild.roles)}
                
                :hash: **Categories:** {len(guild.categories)}
                :speech_balloon:** Text channels:** {len(guild.text_channels)}
                :speaker: **Voice channels:** {len(guild.voice_channels)}
                """)
        embed.set_thumbnail(url=guild.icon_url)

        await ctx.send(embed=embed)

    @info.command(name='bot', description='Show information about bot', help='')
    async def info_bot(self, ctx:commands.Context):
        embed = discord.Embed(title='Information about Asteroid Bot', color=self.bot.get_embed_color(ctx.guild.id))

        users_amount = sum(len(guild.members) for guild in self.bot.guilds)

        embed.description = f"""
                            **Owner:** **Damego#8659**
                            **Current version:** `{version}`
                            **Server\'s amount:** `{len(ctx.bot.guilds)}`
                            **User\'s amount:** `{users_amount}`
                            **Total commands:** `{len(ctx.bot.commands)}`
                            **Latency:** `{int(ctx.bot.latency * 1000)}` ms
                            """

        await ctx.send(embed=embed)


    @commands.command(name='qr', description='Create QR-code', help='[text]')
    async def create_qr(self, ctx, *, text):
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1
        )
        qr.add_data(data=text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f'./qrcodes/{ctx.message.author.id}.png')
        await ctx.send(file = discord.File(f'./qrcodes/{ctx.message.author.id}.png'))
        remove(f'./qrcodes/{ctx.message.author.id}.png')


    @commands.command(description='Show bot latency', help='')
    async def ping(self, ctx):
        embed = discord.Embed(title='🏓 Pong!', description=f'Bot latency is `{int(ctx.bot.latency * 1000)}` мс', color=self.bot.get_embed_color(ctx.guild.id))
        await ctx.send(embed=embed)


    @commands.group(name='send',
        description='Send message in channel',
        help='[channel] [message]',
        invoke_without_command=True,
        usage='Only for Admins')
    @is_administrator_or_bot_owner()
    async def send_message(self, ctx, channel:discord.TextChannel, *, message):
        await channel.send(message)

    @send_message.command(name='delay',
        description='Send delay message in channel',
        help='[channel] [time] [message]',
        usage='Only for Admins')
    @is_administrator_or_bot_owner()
    async def delay_send_message(self, ctx, channel:discord.TextChannel, duration:DurationConverter, *, message):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])
        await channel.send(message)


    @commands.group(name='embed',
        description='Send embed message in channel',
        help='[channel] ["title"] ["description"]',
        invoke_without_command=True,
        usage='Only for Admins')
    @is_administrator_or_bot_owner()
    async def embed_message(self, ctx, channel:discord.TextChannel, title, description):
        embed = discord.Embed(title=title, description=description, color=self.bot.get_embed_color(ctx.guild.id))
        await channel.send(embed=embed)


    @embed_message.command(name='delay',
        description='Send delay embed message in channel',
        help='[channel] [time] ["title"] ["description"]',
        usage='Only for Admins')
    @is_administrator_or_bot_owner()
    async def delay(self, ctx, channel:discord.TextChannel, duration:DurationConverter, title, description):
        amount, time_format = duration
        await sleep(amount * multiplier[time_format])

        embed = discord.Embed(title=title, description=description, color=self.bot.get_embed_color(ctx.guild.id))
        await channel.send(embed=embed)


    @commands.command(name='hltv', description='Upcoming games for CS:GO team', help='[team]')
    async def hltv(self, ctx:commands.Context, *, team):
        hltv = HLTV(self.bot)
        await hltv.parse_mathes(ctx, team)

    @commands.command(
    name='activity',
    description='Start discord Activities',
    help='')
    async def start_activity(self, ctx:commands.Context):
        if not ctx.author.voice:
            return await ctx.send('Connect to voice channel!')

        channel_id = ctx.author.voice.channel.id
        await ctx.send('Choose Activity',
            components=[
                [
                    Button(style=ButtonStyle.red, label='YouTube', id='755600276941176913'),
                    Button(style=ButtonStyle.blue, label='Betrayal.io', id='773336526917861400'),
                    Button(style=ButtonStyle.blue, label='Fishington.io', id='814288819477020702'),
                    Button(style=ButtonStyle.gray, label='Poker Night', id='755827207812677713'),
                    Button(style=ButtonStyle.green, label='Chess', id='832012774040141894'),
                ]
            ]
        )

        interaction:Interaction = await self.bot.wait_for(
            'button_click',
            check=lambda inter: inter.user.id == ctx.author.id)

        data = self._get_data(int(interaction.custom_id))
        headers = {
            'Authorization': f'Bot {environ.get("TOKEN")}',
            'Content-Type': 'application/json'
        }

        responce = requests.post(f'https://discord.com/api/v8/channels/{channel_id}/invites', data=json.dumps(data), headers=headers)
        code = json.loads(responce.content).get('code')

        await interaction.respond(type=6)
        await interaction.message.delete()
        await ctx.send(f'https://discord.com/invite/{code}')


    @commands.command(
    name='roles',
    description='Show guild roles',
    help='')
    async def roles(self, ctx:commands.Context):
        roles = ctx.guild.roles[::-1]
        content = ''.join(
            f'**{count}.** {role.mention}\n' for count, role in enumerate(roles, start=1)
        )

        embed = discord.Embed(
            title='Server Roles',
            description=content,
            color=self.bot.get_embed_color(ctx.guild.id)
        )
        await ctx.send(embed=embed)


    def _get_data(self, application_id: int):
        return {
            'max_age': 86400,
            'max_uses': 0,
            'target_application_id': application_id,
            'target_type': 2,
            'temporary': False,
            'validate': None
        }



def setup(bot):
    bot.add_cog(Misc(bot))