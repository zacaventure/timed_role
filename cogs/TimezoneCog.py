from cogs.WriteCog import WriteCog
from discord import Option, Embed, default_permissions, ApplicationContext
from discord.commands import slash_command
from constant import guildIds
import pytz
import datetime

class TimezoneCog(WriteCog):
    def __init__(self, bot):
        super().__init__(bot)

    @slash_command(guild_ids=guildIds, description="Update the timezone of the server")
    @default_permissions(manage_roles=True)
    async def set_timezone(self, ctx: ApplicationContext, timezone: Option(str, "The timezone for your server")):
        await ctx.defer()
        if timezone not in pytz.all_timezones:
            await ctx.respond("Invalid timezone, check all available timezone here : {}".format("https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"))
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
            
    @slash_command(guild_ids=guildIds, description="Show the timezone of the server")
    async def show_timezone(self, ctx: ApplicationContext):
        await ctx.defer()
        timezone = await self.database.get_timezone(ctx.guild_id)
        if timezone is None:
            await ctx.respond("You did not set a timezone yet ! use /set_timezone <timezone> to set one")
        else:
            await ctx.respond("The timezone for your server is {} and it is currently {} !".format(timezone, datetime.datetime.now(tz=pytz.timezone(timezone)).strftime("%Y-%m-%d at %H:%M:%S")))