import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from discord.ext.commands import has_permissions
from constant import guildIds
from data import Data
import pytz
import datetime

class TimezoneCog(commands.Cog):
    def __init__(self, bot, data: Data):
        self.bot = bot
        self.data = data

    @slash_command(guild_ids=guildIds, description="Update the timezone of the server")
    @has_permissions(manage_roles=True)
    async def set_timezone(self, ctx, timezone: discord.Option(str, "The timezone for your server")):
        await ctx.defer()
        if timezone not in pytz.all_timezones:
            await ctx.respond("Invalid timezone, check all available timezone here : {}".format("https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"))
        else:
            server = self.data.getServer(ctx.guild.id)
            server.timezone = pytz.timezone(timezone)
            self.data.saveData()
            await ctx.respond("The timezone for your server have been updated !")
            
    @slash_command(guild_ids=guildIds, description="Show the timezone of the server")
    async def show_timezone(self, ctx):
        await ctx.defer()
        server = self.data.getServer(ctx.guild.id)
        if server.timezone is None:
            await ctx.respond("You did not set a timezone yet ! use /set_timezone <timezone> to set one")
        else:
            await ctx.respond("The timezone for your server is {} and it is currently {} !".format(server.timezone, datetime.datetime.now(tz=server.timezone).strftime("%Y-%m-%d at %H:%M:%S")))