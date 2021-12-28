import discord
from discord.ext import commands
import os
from dotenv import load_dotenv


# load .env variables
load_dotenv()

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='$', intents = intents)
# data = Data()

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.command(pass_context = True , aliases=["addTimeRole", "atr"])
async def _addTimedRole(ctx, *args):
    pass
@bot.command(pass_context = True , aliases=["removeTimeRole", "rtr"])
async def _removeTimedRole(ctx, *args):
    pass

@bot.event
async def on_member_update(before, after):
    print('roles {}'.format(before.roles))

bot.run(os.getenv('TOKEN'))