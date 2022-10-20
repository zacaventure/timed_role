import asyncio
from constant import datetime_strptime
from typing import List
import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from constant import guildIds
import datetime
from discord.ext.commands import Bot
import database.database as database
import pytz

def add_member_time_role_to_member(members: List[discord.Member], role: discord.Role, timedelta, guild_id):
        # Adding a time role to all member who already have the role
        for memberDiscord in members:
            if role in memberDiscord.roles:
                database.insert_member_time_role_sync(
                    role.id, timedelta,  memberDiscord.id, guild_id)

class AddCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        
    def canTheBotHandleTheRole(self, ctx: discord.ApplicationContext, role: discord.Role) -> bool:
        myBot: discord.Member = ctx.guild.get_member(self.bot.user.id)
        if myBot.top_role.position > role.position:
            return True
        return False

    @slash_command(guild_ids=guildIds, description="Add a new global time role with a expiration date.")    
    @discord.default_permissions(manage_roles=True)
    async def add_global_timed_role(self, ctx: discord.ApplicationContext,
                                    role: discord.Option(discord.Role, "The role that will be added as a global timed role of your server"),
                                    year: discord.Option(int, "The year when the global role expire", min_value=1),
                                    month: discord.Option(int, "The month when the global role expire", min_value=1, max_value=12),
                                    day: discord.Option(int, "The day when the global role expire", min_value=1, max_value=31),
                                    hour : discord.Option(int, "The hour when the global role expire", min_value=0, max_value=23, default=0), 
                                    minute : discord.Option(int, "The minute when the global role expire", min_value=0, max_value=60, default=0)):
        await ctx.defer()
        if not self.canTheBotHandleTheRole(ctx, role):
            await ctx.respond("That role {} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
            return
        timezone = await database.get_timezone(ctx.guild_id)
        if timezone is None:
            end_datatime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        else:
            end_datatime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=pytz.timezone(timezone))
        previous_datetime = await database.insert_global_time_role(role.id, end_datatime, 
                                                                   ctx.guild_id, True)
        embed = None
        if previous_datetime is not None:
            embed = discord.Embed(
                title="Global time role added updated !",
                description="The global role {} already exist with end date of {} ... Updating end date to **{}**".format(
                    role.mention, previous_datetime, end_datatime.strftime(datetime_strptime)))
        else:
            embed = discord.Embed(
                title="Global time role added sucessfully !",
                description="The time role {} was added to the global timed role of the server with a expiration date of **{}**".format(
                    role.mention, end_datatime.strftime(datetime_strptime)))
        await ctx.respond(embed=embed)
    

    @slash_command(guild_ids=guildIds, description="Add a server timed role.Users getting that role will get a timed role")    
    @discord.default_permissions(manage_roles=True)
    async def add_timed_role_to_server(self, ctx: discord.ApplicationContext, role: discord.Option(discord.Role, "The Role that will be a time role for yoru server"),
                                    days: discord.Option(int, "The number of days before the role expire", min_value=0),
                                    hours : discord.Option(int, "The number of hours days before the role expire (is adding time on top of days)", min_value=0, default=0), 
                                    minutes : discord.Option(int, "The number of minutes days before the role expire (is adding time on top of days and hours)", min_value=0, default=0),
                                    add_to_existing_members : discord.Option(bool, "If the bot need to give a time role to member who already have the role", default=True)):
        await ctx.defer()
        timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        if not self.canTheBotHandleTheRole(ctx, role):
            await ctx.respond("That role {} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
            return
        previous_deltime = await database.insert_time_role(role.id, timedelta, ctx.guild_id)
        embed = None
        if previous_deltime is not None:
            description="""The time role {} with a deltatime of {} was updated to {}
            *Note: All member getting the role {} will now only have the role for {}*""".format(
                role.mention,
                datetime.timedelta(seconds=previous_deltime),
                timedelta,
                role.mention,
                timedelta
                )
            embed = discord.Embed(
            title="Server time role was updated sucessfully ! ",
            description=description
            )
        else:
            description="""All member getting the role {} will now only have the role for {}\n""".format(role.mention, timedelta)
            if add_to_existing_members:
                description += "*Note: add_to_existing_members is True (optional parameter) -> All member that already have the role {} will also get a time role (it may take a while for big servers)*".format(role.mention)
            else:
                description += "*Note: add_to_existing_members is False (optional parameter) -> All member that already have the role {} will **NOT** get a time role*".format(role.mention)
            embed = discord.Embed(
            title="Server time role added sucessfully !",
            description=description) 
        await ctx.respond(embed=embed)
        
        if add_to_existing_members:
            # run in a other thread because can be CPU heavy when big guilds
            await asyncio.to_thread(add_member_time_role_to_member, ctx.guild.members, role, timedelta, ctx.guild_id)

   
    @slash_command(guild_ids=guildIds, description="Manually add a timed role to a user")            
    @discord.default_permissions(manage_roles=True)
    async def add_timed_role_to_user(self, ctx: discord.ApplicationContext,
                                    member: discord.Option(discord.Member, "The member that will reecive the time role"),
                                    role: discord.Option(discord.Role, "The Role that will be a time role for the member"),
                                    days: discord.Option(int, "The number of days before the role expire", min_value=0),
                                    hours : discord.Option(int, "The number of hours days before the role expire (is adding time on top of days)", min_value=0, default=0), 
                                    minutes : discord.Option(int, "The number of minutes days before the role expire (is adding time on top of days and hours)", min_value=0, default=0)):
        await ctx.defer()
        member: discord.Member
        if not self.canTheBotHandleTheRole(ctx, role):
            await ctx.respond("That role {} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
            return
        timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        await database.insert_if_not_exist_guild(ctx.guild_id)
        previous_timedelta_seconds  = await database.insert_or_update_member_time_role(role.id, timedelta, member.id, ctx.guild_id)
        if role not in member.roles:
            await member.add_roles(role)
                
        if previous_timedelta_seconds is None:
            embed = discord.Embed(
                title="Custom role delivered sucess !",
                description="The time role {} was deliver to {} with a time delta of {}".format(role.mention, member.mention, timedelta))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(title="Already have that time role", description="{} already has {} as a time role. The user now have {} left ! (updated the expiration time from {})".format(
                member.mention, role.mention, timedelta, datetime.timedelta(seconds=previous_timedelta_seconds)))
            await ctx.respond(embed=embed) 