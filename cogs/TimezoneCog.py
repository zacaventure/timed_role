from discord import Option, Embed, SlashCommandGroup, default_permissions, ApplicationContext
from discord.ext.commands import Cog

from constant import guildIds
import pytz
import datetime

class TimezoneCog(Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.database = bot.database

    TIMEZONE_GROUP = SlashCommandGroup("timezone", "Command group to manipulate timezone of your server")

    @TIMEZONE_GROUP.command(guild_ids=guildIds, name="set", description="Update the timezone of the server")
    @default_permissions(manage_roles=True)
    async def set_timezone(self, ctx: ApplicationContext, timezone: Option(str, "The timezone for your server")):
        await ctx.defer()
        if timezone not in pytz.all_timezones:
            url = "https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"
            embed = Embed(
                title="Invalid timezone",
                color=0xFF0000,
                description=f"Invalid timezone, check all available timezone [here]({url})"
            )
            await ctx.respond(embed=embed)
        else:
            old_timezone = await self.database.insert_or_update_timezone(timezone, ctx.guild_id)
            now = datetime.datetime.now(tz=pytz.timezone(timezone)).strftime("%Y-%m-%d at %H:%M:%S")
            if old_timezone is not None:
                if  old_timezone == timezone:
                    await ctx.respond(f"You already have that timezone set: {old_timezone}")
                    return
                embed = Embed(
                    title="Update sucess !",
                    description="The timezone was change from {} to {}\n It is now {}".format(old_timezone, timezone, now))
                await ctx.respond(embed=embed)
            else:
                embed = Embed(
                    title="Insert sucess !",
                    description="The timezone was set to {}\n It is now {}".format(timezone, now))
                await ctx.respond(embed=embed)
            await self.database.commit()
            
    @TIMEZONE_GROUP.command(guild_ids=guildIds, name="show", description="Show the timezone of the server")
    async def show_timezone(self, ctx: ApplicationContext):
        await ctx.defer()
        timezone = await self.database.get_timezone(ctx.guild_id)
        if timezone is None:
            commands_dict = self.bot.get_commands_as_dict()
            slash_command = commands_dict.get("timezone set")
            embed = Embed(
                title="Invalid timezone",
                color=0xFF0000,
                description=f"You did not set a timezone yet ! Set {slash_command.mention} <timezone> to set one")
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("The timezone for your server is {} and it is currently {} !".format(timezone, datetime.datetime.now(tz=pytz.timezone(timezone)).strftime("%Y-%m-%d at %H:%M:%S")))
