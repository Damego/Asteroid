import discord
from discord.ext import commands
import json
import os
from replit import Database, db
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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
            m_id = 0
            day = upc.find('span', class_='matchDayHeadline').get_text(strip=True)
            matches = upc.find_all('div', class_='upcomingMatch')
            ls[str(day)] = {}

            for match in matches:
                
                if (match.find('div',class_='matchTeam') == None) or (match.find('div',class_='matchTeam').text == 'TDB'):
                    pass
                else:
                    m_id +=1
                    ls[str(day)][str(m_id)] = {
                        'team1': match.find('div',class_='matchTeam team1').get_text(strip=True),
                        'team2': match.find('div',class_='matchTeam team2').get_text(strip=True),
                        'time': match.find('div',class_='matchTime').get_text(strip=True)
                    }
        return ls

    async def parse(self, ctx, arg):
        embed = discord.Embed(title='Расписание игр по CS:GO', description=f'Ближайшие игры команды {arg}', color = get_embed_color(ctx.message))

        html = self.get_html(self.URL)
        if html.status_code == 200:
            matches_data = []
            html = self.get_html(self.URL)
            matches_data = self.get_content(html.text)

            for day in matches_data:
                flag = True
                
                m_id = 1
                date = day.split(' ')[2]
                in_day_data = matches_data.get(str(day))

                new_date = datetime.strptime(date, '%Y-%m-%d')
                date = new_date.strftime('%d.%m.%Y')
                
                

                for match in in_day_data:
                    match_data = in_day_data.get(str(m_id))
                    if match_data['team1'] == arg or match_data['team2'] == arg:
                        if flag:
                                embed.add_field(name='\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_', value=f'**{date}**')
                                flag = False
                        if match_data is not None:
                            time = datetime.strptime(match_data['time'], '%H:%M') + timedelta(hours=3)
                            embed.add_field(name='===========', value="""
                            Время: {}
                            Команды: {} и {}
                            """.format(time.strftime('%H:%M'), match_data['team1'], match_data['team2']), inline=False)
                    
                    m_id +=1
            await ctx.send(embed=embed)

    @commands.command()
    async def games(self, ctx, *, arg):
        await self.parse(ctx, arg)

def setup(bot):
    bot.add_cog(HLTV(bot))