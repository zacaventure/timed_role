from cogs.WriteCog import WriteCog
from constant import datetime_strptime

import discord
from discord import Color, Role
from constant import guildIds
import datetime
import pytz

from views.RecurrentRoleAddUpdateView import RecurrentRoleAddUpdateView, generate_edit_embed, generate_insert_embed

class AddCog(WriteCog):
    def __init__(self, bot):
        super().__init__(bot)

    ADD_OR_UDPATE_GROUP = discord.SlashCommandGroup("add-update", "Command group to add or update various timed role types")

    @ADD_OR_UDPATE_GROUP.command(guild_ids=guildIds, name="global_timed_role", description="Add a new global time role with a expiration date.")    
    @discord.default_permissions(manage_roles=True)
    async def add_global_timed_role(self, ctx: discord.ApplicationContext,
                                    role: discord.Option(discord.Role, "The role that will be added as a global timed role of your server"),
                                    year: discord.Option(int, "The year when the global role expire", min_value=1),
                                    month: discord.Option(int, "The month when the global role expire", min_value=1, max_value=12),
                                    day: discord.Option(int, "The day when the global role expire", min_value=1, max_value=31),
                                    hour : discord.Option(int, "The hour when the global role expire", min_value=0, max_value=23, default=0), 
                                    minute : discord.Option(int, "The minute when the global role expire", min_value=0, max_value=60, default=0)):
        await ctx.defer()
        timezone = await self.database.get_timezone(ctx.guild_id)
        now = datetime.datetime.now()
        if timezone is None:
            end_datatime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        else:
            now = datetime.datetime.now(tz=pytz.timezone(timezone))
            end_datatime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=pytz.timezone(timezone))
        
        if end_datatime.strftime(datetime_strptime) < now.strftime(datetime_strptime):
            timezone_str = " with no timezone set"
            if timezone is not None:
                timezone_str = f" in {timezone}"
            embed = discord.Embed(
                title="Invalid end datetime",
                color=0xFF0000,
                description=f"The end date {end_datatime.strftime(datetime_strptime)} is in the past. \nCurrent date: {now.strftime(datetime_strptime)} {timezone_str}")
            embed.set_footer(text="Remember to verify the timezone of your serveur")
            await ctx.respond(embed=embed)
            return
        embed = None
        previous_datetime = await self.database.insert_or_update_global_time_role(role.id, end_datatime, 
                                                                   ctx.guild_id, True)
        if previous_datetime is not None:
            embed = discord.Embed(
                title="Global time role added updated !",
                color=Color.green(),
                description="The global role {} already exist with end date of {} ... Updating end date to **{}**".format(
                    role.mention, previous_datetime, end_datatime.strftime(datetime_strptime)))
        else:
            embed = discord.Embed(
                title="Global time role added sucessfully !",
                color=Color.green(),
                description="The time role {} was added to the global timed role of the server with a expiration date of **{}**".format(
                    role.mention, end_datatime.strftime(datetime_strptime)))
        await self.database.commit()
        await ctx.respond(embed=embed)
    

    @ADD_OR_UDPATE_GROUP.command(guild_ids=guildIds, name="server_time_role", description="Add a server timed role.Users getting that role will get a timed role")    
    @discord.default_permissions(manage_roles=True)
    async def add_timed_role_to_server(self, ctx: discord.ApplicationContext, role: discord.Option(discord.Role, "The Role that will be a time role for yoru server"),
                                    days: discord.Option(int, "The number of days before the role expire", min_value=0),
                                    hours : discord.Option(int, "The number of hours days before the role expire (is adding time on top of days)", min_value=0, default=0), 
                                    minutes : discord.Option(int, "The number of minutes days before the role expire (is adding time on top of days and hours)", min_value=0, default=0)):
        await ctx.defer()
        timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        previous_deltime = await self.database.insert_or_update_time_role(role.id, timedelta, ctx.guild_id)
        embed = None
        if previous_deltime is not None:
            description="""The time role {} with a deltatime of {} was updated to {}
            *Note: All member getting the role {} will now only have the role for {}*""".format(
                role.mention,
                previous_deltime,
                timedelta,
                role.mention,
                timedelta
                )
            embed = discord.Embed(
                title="Server time role was updated sucessfully ! ",
                color=Color.green(),
                description=description
            )
        else:
            description=f"All member getting the role {role.mention} will now only have the role for {timedelta}\n"
            description += f"*Note: All member that already have the role {role.mention} will also get a time role (it may take a while for big servers)*"
            embed = discord.Embed(
                title="Server time role added sucessfully !",
                color=Color.green(),
                description=description
            ) 
        await ctx.respond(embed=embed)
        
        for member in role.members:
            await self.database.insert_or_update_member_time_role(role.id, timedelta, member.id, ctx.guild_id)

        await self.database.commit()

   
    @ADD_OR_UDPATE_GROUP.command(guild_ids=guildIds, name="time_role", description="Manually add a timed role to a user")            
    @discord.default_permissions(manage_roles=True)
    async def add_timed_role_to_user(self, ctx: discord.ApplicationContext,
                                    member: discord.Option(discord.Member, "The member that will reecive the time role"),
                                    role: discord.Option(discord.Role, "The Role that will be a time role for the member"),
                                    days: discord.Option(int, "The number of days before the role expire", min_value=0),
                                    hours : discord.Option(int, "The number of hours days before the role expire (is adding time on top of days)", min_value=0, default=0), 
                                    minutes : discord.Option(int, "The number of minutes days before the role expire (is adding time on top of days and hours)", min_value=0, default=0)):
        await ctx.defer()
        if not isinstance(member, discord.Member):
            await ctx.respond(f"That user is not in your guild anymore (but can still be in your cache)")
            return
        timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        await self.database.insert_if_not_exist_guild(ctx.guild_id)
        previous_timedelta_seconds  = await self.database.insert_or_update_member_time_role(role.id, timedelta, member.id, ctx.guild_id)
        if role not in member.roles:
            await member.add_roles(role)
                
        if previous_timedelta_seconds is None:
            embed = discord.Embed(
                title="Custom role delivered successfully !",
                color=Color.green(),
                description="The time role {} was deliver to {} with a time delta of {}".format(role.mention, member.mention, timedelta))
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(title="Already have that time role", color=Color.green(), description="{} already has {} as a time role. The user now have {} left ! (updated the expiration time from {})".format(
                member.mention, role.mention, timedelta, datetime.timedelta(seconds=previous_timedelta_seconds)))
            await ctx.respond(embed=embed)
        await self.database.commit()

    @ADD_OR_UDPATE_GROUP.command(guild_ids=guildIds, name = "recurrent_timed_role", description="Add a new recurrent timed role")
    @discord.default_permissions(manage_roles=True)
    @discord.option(
        "role",
        description="Enter the discord role to become recurrent timed role",
        type=Role
    )
    async def add_recurrent_time_role(self, ctx: discord.ApplicationContext, role: Role):
        timezone = await self.database.get_timezone(ctx.guild_id)
        if timezone is None:
            timezone_str = "not set"
            now = datetime.datetime.now()
        else:
            timezone_str = str(timezone)
            now = datetime.datetime.now(tz=pytz.timezone(timezone))

        
        recurrent_role = await self.database.get_recurrent_time_role(role.id, ctx.guild_id)
        if recurrent_role is None:
            embed = generate_insert_embed(role.mention, None, None, timezone)
            view = RecurrentRoleAddUpdateView(ctx.guild_id, self.database, role, now, ctx.author.id)
        else:
            start_datetime = datetime.datetime.strptime(recurrent_role[2], datetime_strptime)
            next_datetime = datetime.datetime.strptime(recurrent_role[3], datetime_strptime)
            current_interval = datetime.timedelta(seconds=recurrent_role[4])
            embed = generate_edit_embed(role.mention, start_datetime, current_interval, timezone_str, next_datetime)
            return await ctx.respond(embed=embed)
            """ currently does not support editing (can create strange interaction) # TODO
            date_data = {
                "year": start_datetime.year,
                "month": start_datetime.month,
                "day": start_datetime.day
            }
            time_data = {
                "hours": start_datetime.hour,
                "minutes": start_datetime.minute,
                "seconds": start_datetime.second,
            }
            delta_split = str(current_interval).split(",")
            time_split = delta_split[1].strip().split(":")
            delta_data = {
                "days_delta": current_interval.days,
                "hours_delta": int(time_split[0]),
                "minutes_delta": int(time_split[1]),
                "seconds_delta": int(time_split[2])
            }
            view = MyView(ctx.guild_id, self.database, role, now, ctx.author.id, date_data=date_data, time_data=time_data, delta_data=delta_data)
        """
        interaction = await ctx.respond(embed=embed, view=view)
        view.set_origin_interaction(interaction)