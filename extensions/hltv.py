from datetime import datetime, timedelta

import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup


from extensions.bot_settings import get_embed_color


class HLTV(commands.Cog, description='HLTV'):
    def __init__(self, bot):
        self.bot = bot
        self.hidden = False
        self.aliases = ['hltv']

        self.URL = 'https://www.hltv.org/matches'
        self.HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': '*/*'}

    def get_html(self, url, params=None):
        return requests.get(self.URL, headers=self.HEADERS, params=params)

    def get_content(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        upcomingmatches = soup.find_all('div', class_='upcomingMatchesSection')
        ls = {}
    
        for upc in upcomingmatches:
            match_id = 0
            day = upc.find('span', class_='matchDayHeadline').get_text(strip=True)
            matches = upc.find_all('div', class_='upcomingMatch')
            ls[str(day)] = {}

            for match in matches:
                
                if (match.find('div',class_='matchTeam') is not None):
                    match_id +=1
                    ls[str(day)][str(match_id)] = {
                        'team1': match.find('div',class_='matchTeam team1').get_text(strip=True),
                        'team2': match.find('div',class_='matchTeam team2').get_text(strip=True),
                        'time': match.find('div',class_='matchTime').get_text(strip=True),
                        'event': match.find('div', class_='matchEventName').get_text(strip=True),
                        'format': match.find('div', class_='matchMeta').get_text(strip=True)
                    }
                    
        return ls

    async def parse(self, ctx, team):
        embed = discord.Embed(title='Расписание игр по CS:GO', description=f'Ближайшие игры команды {team}', color=get_embed_color(ctx.guild.id))

        html = self.get_html(self.URL)
        if html.status_code == 200:
            all_days = self.get_content(html.text)

            for day in all_days:
                date_was_printed = False
                date = day.split(' ')[2]
                date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
                matches_in_day = all_days.get(str(day))

                for match in matches_in_day:
                    match_data = matches_in_day.get(str(match))
                    if match_data['team1'] == team or match_data['team2'] == team:
                        if not date_was_printed:
                                embed.add_field(name='\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_', value=f'**{date}**')
                                date_was_printed = True
                        if match_data is not None:
                            time = (datetime.strptime(match_data['time'], '%H:%M') + timedelta(hours=3)).strftime('%H:%M')
                            embed.add_field(name='==================', value="""
                            Время: {}
                            Команды: {} и {}
                            Событие: {}
                            Формат: {}
                            """.format(time, match_data['team1'], match_data['team2'], match_data['event'], match_data['format'].replace('bo', 'Best of ')), inline=False)
                    
            await ctx.send(embed=embed)

    @commands.command(name='hltv', description='Выводит дату ближайщих игр указанной комадны', help='[команда]')
    async def hltv(self, ctx:commands.Context, *, team):
        await self.parse(ctx, team)

def setup(bot):
    bot.add_cog(HLTV(bot))