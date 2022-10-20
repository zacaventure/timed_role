from time import timezone
import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from constant import guildIds
import pytz
import datetime
import database.database as database

class TimezoneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(guild_ids=guildIds, description="Update the timezone of the server")
    @discord.default_permissions(manage_roles=True)
    async def set_timezone(self, ctx, timezone: discord.Option(str, "The timezone for your server")):
        await ctx.defer()
        if timezone not in pytz.all_timezones:
            await ctx.respond("Invalid timezone, check all available timezone here : {}".format("https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"))
        else:
            old_timezone = await database.insert_timezone(timezone, ctx.guild_id)
            now = datetime.datetime.now(tz=pytz.timezone(timezone)).strftime("%Y-%m-%d at %H:%M:%S")
            if old_timezone is not None:
                embed = discord.Embed(
                    title="Update sucess !",
                    description="The timezone was change from {} to {}\n It is now {}".format(old_timezone, timezone, now))
                await ctx.respond(embed=embed)
            else:
                embed = discord.Embed(
                    title="Insert sucess !",
                    description="The timezone was set to {}\n It is now {}".format(timezone, now))
                await ctx.respond(embed=embed)
            
    @slash_command(guild_ids=guildIds, description="Show the timezone of the server")
    async def show_timezone(self, ctx):
        await ctx.defer()
        timezone = await database.get_timezone(ctx.guild_id)
        if timezone is None:
            await ctx.respond("You did not set a timezone yet ! use /set_timezone <timezone> to set one")
        else:
            await ctx.respond("The timezone for your server is {} and it is currently {} !".format(timezone, datetime.datetime.now(tz=pytz.timezone(timezone)).strftime("%Y-%m-%d at %H:%M:%S")))