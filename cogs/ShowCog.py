from discord import ApplicationContext, Role, Option, Member, Embed
from discord.commands import slash_command
from discord.ext import commands
from discord.utils import get

from cogs.Util import get_paginator
from constant import guildIds, datetime_strptime
import datetime
import pytz

from database.database import Database


class ShowCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database: Database = self.bot.database

    @slash_command(guild_ids=guildIds, description="Show all the individual and global timed role of your server")
    async def show_timed_role_of_server(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=True)
        
        server_time_roles = await self.database.get_all_server_time_roles(ctx.guild_id)
        server_time_roles.sort(key=lambda x: x[1]) # Sort with expiration days
                
        value_server=""
        i = 1
        for roleId, timedelta_s in server_time_roles:
            role_get: Role = ctx.guild.get_role(roleId)
            if role_get is None:
                try:
                    role_get: Role = await ctx.guild._fetch_role(roleId)
                except:
                    pass
            timedelta = datetime.timedelta(seconds=timedelta_s)
            if role_get is not None:
                value_server += "{}) {} with a time delta of {} \n".format(i, role_get.mention, str(timedelta).split(".")[0])
                i += 1
        if value_server == "":
            value_server = "No timed role for your server" 
        paginator_server = get_paginator(value_server, titles="Timed role of your server")
        
        
        value_global=""
        i = 1
        global_time_roles = await self.database.get_all_global_time_roles(ctx.guild_id)
        timezone = await self.database.get_timezone(ctx.guild_id)
        global_time_roles.sort(key=lambda x: x[1]) # Sort with end date
        for id, end_datetime in global_time_roles:
            role_get: Role = ctx.guild.get_role(id)
            if role_get is None:
                try:
                    role_get: Role = await ctx.guild._fetch_role(id)
                except:
                    pass
            if role_get is not None:
                if timezone is None:
                    value_global += "{}) {} expire on {} \n".format(i, role_get.mention, end_datetime)
                else:
                    value_global += "{}) {} expire on {} in {} \n".format(i, role_get.mention, end_datetime, timezone)
                i += 1
        if value_global == "":
            value_global = "No global timed role for your server"
        paginator_global = get_paginator(value_global,
                                         titles="Global timed role of your server",
                                         footers="Note: Global roles expire for everyone in the server at the same time !")
            
        await paginator_server.respond(ctx.interaction, ephemeral=True)
        await paginator_global.respond(ctx.interaction, ephemeral=True)
        
    @slash_command(guild_ids=guildIds, description="Show all the individual and global timed role of a member")
    async def show_timed_role_of_member(self, ctx: ApplicationContext,
                                        member: Option(Member, "The member which roles will be show")):
        await ctx.defer(ephemeral=True)

        member_time_roles = await self.database.get_member_time_role(member.id, ctx.guild_id)
        remaining_time = []
        for member_time_role in member_time_roles:
            start_time = datetime.datetime.strptime(member_time_role[1].strip(), datetime_strptime)
            deltatime = datetime.datetime.now() - start_time
            remaining_time.append((member_time_role[0], datetime.timedelta(seconds=member_time_role[2]) - deltatime))
        remaining_time.sort(key=lambda x: x[1]) # sort by remaining time
        value=""
        i = 1   
        for role_with_time in remaining_time:
            role_get = get(ctx.guild.roles, id=role_with_time[0])
            if role_get is not None:
                value += "{}) {} with {} left\n".format(i, role_get.mention, str(role_with_time[1]).split(".")[0])
                i += 1
        if value == "":
            value = "No timed role for {}".format(member.name) 
        paginator_server = get_paginator(value, titles="Timed role of {}".format(member.name))
        
        
        global_time_roles = await self.database.get_all_global_time_roles(ctx.guild_id)
        global_time_roles.sort(key=lambda x: x[1]) # Sort with end date
        timezone = await self.database.get_timezone(ctx.guild_id)
        value=""
        i = 1
        for id, end_datetime in global_time_roles:
            role_get: Role = ctx.guild.get_role(id)
            if role_get is None:
                try:
                    role_get: Role = await ctx.guild._fetch_role(id)
                except:
                    pass
            if role_get in member.roles and role_get is not None:
                if timezone is None:
                    value += "{}) {} that expire for everyone on {} \n".format(i, role_get.mention, end_datetime)
                else:
                    value += "{}) {} that expire for everyone on {} in {} \n".format(i, role_get.mention, end_datetime, timezone)
            i += 1
        if value == "":
            value = "No global timed role for {}".format(member.name) 
        paginator_global = get_paginator(value, titles="Global timed role of {}".format(member.name))
        
        await paginator_server.respond(ctx.interaction, ephemeral=True)
        await paginator_global.respond(ctx.interaction, ephemeral=True)
        
    async def send_member_time_role_response(self, role: Role, ctx,
                                             timedelta_remaining: datetime.timedelta = None):
            member_time_roles = await self.database.get_member_time_role_from_guild(role.id, ctx.guild_id)
                
            remaining_times = []
            for member_time_role in member_time_roles:
                start_time = datetime.datetime.strptime(member_time_role[0].strip(), datetime_strptime)
                time_passed = datetime.datetime.now() - start_time
                time_remaining = datetime.timedelta(seconds=member_time_role[1]) - time_passed
                if timedelta_remaining is None:
                    remaining_times.append(
                        (time_remaining, 
                        f"<@{member_time_role[2]}>"))
                elif time_remaining < timedelta_remaining:
                    remaining_times.append(
                        (time_remaining, 
                        f"<@{member_time_role[2]}>"))
                    
                
            remaining_times.sort(key=lambda x: x[0]) # sort by remaining time
            
            value = ""
            i = 1
            for time, member_mention in remaining_times:
                value += "{}) {} with a remaining time of {} \n".format(i, member_mention,
                                                                        str(time).split(".")[0])

            if value == "" and timedelta_remaining is None:
                value = "Nobody have this timed role"
                embed = Embed(
                    title="Member with the time role {}".format(role.name),
                    description="Nobody have this timed role {}".format(role.mention))
                await ctx.respond(embed=embed)
                return
            elif value != "":
                if timedelta_remaining is not None:
                    title = "Member with the time role {} with less time remaining"
                else:
                    title = "Member with the time role {}"
                paginator = get_paginator(value, titles=title.format(role.name))
                await paginator.respond(ctx.interaction, ephemeral=True)
        
    @slash_command(guild_ids=guildIds, description="Show all the user of a timed role. The time until expire is also shown")
    async def show_timed_role_users(self, ctx: ApplicationContext, 
                                    role: Option(Role, "The common role of the members")):
        await ctx.defer(ephemeral=True)
        global_time_role = await self.database.get_global_time_role(role.id, ctx.guild_id)
        
        if global_time_role is None:
            await self.send_member_time_role_response(role, ctx)
        else:
            timezone = await self.database.get_timezone(ctx.guild_id)
            end_datatime = datetime.datetime.strptime(global_time_role[1], datetime_strptime)
            if timezone is None:
                timedelta_remaining = end_datatime - datetime.datetime.now()
            else:
                now = datetime.datetime.now(tz=pytz.timezone(timezone))
                now = datetime.datetime(year=now.year, month=now.month,
                                 day=now.day, hour=now.hour,
                                 minute=now.minute, second=now.second,
                                 microsecond=now.microsecond)
                timedelta_remaining = end_datatime - now
            embed = Embed(
            title="The role {} is a global".format(role.name),
            description="The role {} will expire for everyone at {} \n There is {} time left".format(
                role.mention, global_time_role[1], timedelta_remaining))
            await ctx.respond(embed=embed)
            await self.send_member_time_role_response(role, ctx, timedelta_remaining)
