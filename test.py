import os
import discord
from dotenv import load_dotenv

from data import Data
bot = discord.Bot()
data = Data()

load_dotenv()

guildIds = []
for guild in data.servers:
    guildIds.append(guild.serverId)
    
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.slash_command(guild_ids=guildIds)
async def hello(ctx):
    await ctx.respond("Hello!")

    
bot.run(os.getenv("TOKEN"))