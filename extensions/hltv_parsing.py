import os
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from replit import Database, db
import requests
from bs4 import BeautifulSoup


if db != None:
    server = db
else:
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv('URL')
    server = Database(url)

def get_embed_color(message):
    """Get color for embeds from json """
    return int(server[str(message.guild.id)]['embed_color'], 16)

class HLTV(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL = 'https://www.hltv.org/matches'
        self.HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36', 'accept': '*/*'}

    def get_html(self, url, params=None):
        r = requests.get(self.URL, headers=self.HEADERS, params=params)
        return r

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
                
                if (match.find('div',class_='matchTeam') == None) or (match.find('div',class_='matchTeam').text == 'TDB'):
                    pass
                else:
                    match_id +=1
                    ls[str(day)][str(match_id)] = {
                        'team1': match.find('div',class_='matchTeam team1').get_text(strip=True),
                        'team2': match.find('div',class_='matchTeam team2').get_text(strip=True),
                        'time': match.find('div',class_='matchTime').get_text(strip=True),
                        'event': match.find('div', class_='matchEventName').get_text(strip=True),
                        'format': match.find('div', class_='matchMeta').get_text(strip=True)
                    }
        return ls

    async def parse(self, ctx, arg):
        embed = discord.Embed(title='Расписание игр по CS:GO', description=f'Ближайшие игры команды {arg}', color=get_embed_color(ctx.message))

        html = self.get_html(self.URL)
        if html.status_code == 200:
            all_matches = self.get_content(html.text)

            for day in all_matches:
                flag = True
                date = day.split(' ')[2]
                date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
                in_day_matches = all_matches.get(str(day))

                for match in in_day_matches:
                    match_data = in_day_matches.get(str(match))
                    if match_data['team1'] == arg or match_data['team2'] == arg:
                        if flag:
                                embed.add_field(name='\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_', value=f'**{date}**')
                                flag = False
                        if match_data is not None:
                            time = (datetime.strptime(match_data['time'], '%H:%M') + timedelta(hours=3)).strftime('%H:%M')
                            embed.add_field(name='===========', value="""
                            Время: {}
                            Команды: {} и {}
                            Событие: {}
                            Формат: {}
                            """.format(time, match_data['team1'], match_data['team2'], match_data['event'], match_data['format']), inline=False)
                    
            await ctx.send(embed=embed)

    @commands.command()
    async def subscribe(self, ctx, *, arg):
        ctx.member.add_role(843178317871317054)

    @commands.command()
    async def unsubscribe(self,ctx, *, arg):
        ctx.member.remove_role(843178317871317054)

    @commands.command()
    async def startloop(self,ctx):
        pass


    @tasks.loop(minutes=1)
    async def test_tasks(self, ctx):
        html = self.get_html(self.URL)
        if html.status_code == 200:
            pass

    @commands.command()
    async def games(self, ctx, *, arg):
        await self.parse(ctx, arg)

def setup(bot):
    bot.add_cog(HLTV(bot))