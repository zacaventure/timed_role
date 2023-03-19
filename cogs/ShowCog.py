from discord import ApplicationContext, Role, Member, Embed, SlashCommandGroup, Guild, option
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

    SHOW_GROUP = SlashCommandGroup("show", "Command group to show various timed role types")

    @SHOW_GROUP.command(guild_ids=guildIds, name="all", description="Show all the server, global and recurrent timed role of your server")
    async def show_timed_role_of_server(self, ctx: ApplicationContext):
        await ctx.defer(ephemeral=True)
        timezone = await self.database.get_timezone(ctx.guild_id)
        
        paginator_server = await self.generate_server_time_role_paginator(ctx.guild)
        paginator_global = await self.generate_global_time_role_paginator(ctx.guild, timezone)
        paginator_recurrent = await self.generate_recurrent_time_role_paginator(ctx.guild, timezone)

        await paginator_server.respond(ctx.interaction, ephemeral=True)
        await paginator_global.respond(ctx.interaction, ephemeral=True)
        await paginator_recurrent.respond(ctx.interaction, ephemeral=True)

    async def generate_recurrent_time_role_paginator(self, guild: Guild, timezone: datetime.timedelta, member:Member=None):
        recurrent_roles = await self.database.get_recurrent_time_roles_of_server(guild.id)
        roles = []
        for row in recurrent_roles:
            role, _ = await self.bot.get_or_fetch_role(guild, row[0])
            if role is not None and (member is None or role in member.roles):
                roles.append((role.mention, row[1], datetime.timedelta(seconds=row[2])))
        
        roles.sort()
        description = "No recurrent time role in your server" if len(roles) == 0 else ""
        for index, role_info in enumerate(roles):
            description += f"{index + 1}) {role_info[0]} next expiration on {role_info[1]} (delta={role_info[2]})\n"
        title = "Recurrent time role" if timezone is None else f"Recurrent time role (on timezone {timezone})"
        return get_paginator(description, titles=title)

    async def generate_server_time_role_paginator(self, guild: Guild):
        server_time_roles = await self.database.get_all_server_time_roles(guild.id)
        server_time_roles.sort(key=lambda x: x[1]) # Sort with expiration days
                
        value_server=""
        i = 1
        for roleId, timedelta_s in server_time_roles:
            role, _ = await self.bot.get_or_fetch_role(guild, roleId)
            if role is None:
                continue
            timedelta = datetime.timedelta(seconds=timedelta_s)
            formated_delta = str(timedelta).split(".")[0]
            value_server += f"{i}) {role.mention} with a time delta of {formated_delta} \n"
            i += 1
        if value_server == "":
            value_server = "No timed role for your server" 
        return get_paginator(value_server, titles="Timed role of your server")
    
    async def generate_global_time_role_paginator(self, guild: Guild, timezone: datetime.timedelta, member: Member=None):
        value_global=""
        i = 1
        global_time_roles = await self.database.get_all_global_time_roles(guild.id)
        global_time_roles.sort(key=lambda x: x[1]) # Sort with end date
        for id, end_datetime in global_time_roles:
            role, _ = await self.bot.get_or_fetch_role(guild, id)
            if role is None or (member is not None and not (role in member.roles) ):
                continue
            
            if timezone is None:
                value_global += f"{i}) {role.mention} expire on {end_datetime} \n"
            else:
                value_global += f"{i}) {role.mention} expire on {end_datetime} in {timezone} \n"
            i += 1
        if value_global == "":
            value_global = "No global timed role for your server"

        return get_paginator(
            value_global, titles="Global timed role of your server" if member is None else f"Global timed role of {member.name}",
            footers="Note: Global roles expire for everyone in the server at the same time !"
            )
        
    @SHOW_GROUP.command(guild_ids=guildIds, name="member", description="Show all the individual, global and recurrent timed role of a member")
    @option(
        "role",
        description="The member which roles will be show",
        type=Member
    )
    async def show_timed_role_of_member(self, ctx: ApplicationContext, member: Member):
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
        
        
        timezone = await self.database.get_timezone(ctx.guild_id)
        paginator_global = await self.generate_global_time_role_paginator(ctx.guild, timezone, member=member)
        paginator_recurrent = await self.generate_recurrent_time_role_paginator(ctx.guild, timezone, member=member)
        
        await paginator_server.respond(ctx.interaction, ephemeral=True)
        await paginator_global.respond(ctx.interaction, ephemeral=True)
        await paginator_recurrent.respond(ctx.interaction, ephemeral=True)
        
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
        
    @SHOW_GROUP.command(guild_ids=guildIds, name="role", description="Show all the user of a timed role. The time until expire is also shown")
    @option(
        "role",
        description="The common role of the members",
        type=Role
    )
    async def show_timed_role_users(self, ctx: ApplicationContext, role: Role):
        await ctx.defer(ephemeral=True)

        global_time_role = await self.database.get_global_time_role(role.id, ctx.guild_id)
        recurrent_time_role = await self.database.get_recurrent_time_role(role.id, ctx.guild_id)
        
        if global_time_role is None and recurrent_time_role is None:
            return await self.send_member_time_role_response(role, ctx)

        timezone = await self.database.get_timezone(ctx.guild_id)
        if timezone is None:
            timedelta_remaining = end_datatime - datetime.datetime.now()
        else:
            now = datetime.datetime.now(tz=pytz.timezone(timezone))
            now = datetime.datetime(year=now.year, month=now.month,
                                day=now.day, hour=now.hour,
                                minute=now.minute, second=now.second,
                                microsecond=now.microsecond)
            title = f"The role {role.name} is a "
            description = ""
            if global_time_role is not None:
                end_datatime = datetime.datetime.strptime(global_time_role[1], datetime_strptime)
                timedelta_remaining = end_datatime - now
                title += "global time role and a "
                description += f"The **global** time role {role.mention} will be deleted at {global_time_role[1]}. There is {timedelta_remaining} time left \n"
            if recurrent_time_role is not None:
                end_datatime = datetime.datetime.strptime(recurrent_time_role[3], datetime_strptime)
                timedelta_remaining = end_datatime - now
                title += "recurrent time role"
                description += f"The **recurrent** time role {role.mention} will expire for everyone at {recurrent_time_role[3]}. There is {timedelta_remaining} time left \n"
            if title.endswith("and a "):
                title = title[:-len("and a ")]
        await ctx.respond(embed=Embed(title=title, description=description))

    @SHOW_GROUP.command(guild_ids=guildIds, name = "recurrent_timed_roles", description="Show all recurrent timed role of server")
    async def show_recurrent_time_role(self, ctx: ApplicationContext):
        timezone = await self.database.get_timezone(ctx.guild_id)
        paginator = await self.generate_recurrent_time_role_paginator(ctx.guild, timezone)
        await paginator.respond(ctx.interaction)

    @SHOW_GROUP.command(guild_ids=guildIds, name = "server_timed_roles", description="Show all server timed role of server")
    async def show_recurrent_time_role(self, ctx: ApplicationContext):
        paginator = await self.generate_server_time_role_paginator(ctx.guild)
        await paginator.respond(ctx.interaction)

    @SHOW_GROUP.command(guild_ids=guildIds, name = "global_timed_roles", description="Show all global timed role of server")
    async def show_recurrent_time_role(self, ctx: ApplicationContext):
        timezone = await self.database.get_timezone(ctx.guild_id)
        paginator = await self.generate_global_time_role_paginator(ctx.guild, timezone)
        await paginator.respond(ctx.interaction)