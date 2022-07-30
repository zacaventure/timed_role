import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from constant import guildIds
from data import Data
import datetime

from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.TimedRole import TimedRole

class AddCog(commands.Cog):
    def __init__(self, bot, data: Data):
        self.bot = bot
        self.data = data
        
    def canTheBotHandleTheRole(self, ctx, role: discord.Role) -> bool:
        myBot: discord.Member = ctx.guild.get_member(self.bot.user.id)
        if myBot.top_role.position > role.position:
            return True
        return False

    @slash_command(guild_ids=guildIds, description="Add a new global time role with a expiration date.")    
    @discord.default_permissions(manage_roles=True)
    async def add_global_timed_role(self, ctx, role: discord.Option(discord.Role, "The role that will be added as a global timed role of your server"),
                                    year: discord.Option(int, "The year when the global role expire", min_value=1),
                                    month: discord.Option(int, "The month when the global role expire", min_value=1, max_value=12),
                                    day: discord.Option(int, "The day when the global role expire", min_value=1, max_value=31),
                                    hour : discord.Option(int, "The hour when the global role expire", min_value=0, max_value=23, default=0), 
                                    minute : discord.Option(int, "The minute when the global role expire", min_value=0, max_value=60, default=0)):
        await ctx.defer()
        if not self.canTheBotHandleTheRole(ctx, role):
            await ctx.respond("That role {} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
            return
        server = self.data.getServer(ctx.guild.id)
        for globalTimeRole in server.globalTimeRoles:
            if globalTimeRole.roleId == role.id:
                globalTimeRole.endDate = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=server.timezone)
                await ctx.respond("The global role already exist... updating end date")
                return
        
        globalRole = GlobalTimedRole(role.id, datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, tzinfo=server.timezone))
        server.globalTimeRoles.append(globalRole)
        self.data.saveData()
        embed = discord.Embed(
            title="Global time role added sucessfully !",
            description="The time role {} was added to the global timed role of the server with a expiration date of {}".format(role.mention, globalRole.printEndDate()))
        await ctx.respond(embed=embed)
        
    @slash_command(guild_ids=guildIds, description="Add a server timed role.Users getting that role will get a timed role")    
    @discord.default_permissions(manage_roles=True)
    async def add_timed_role_to_server(self, ctx, role: discord.Option(discord.Role, "The Role that will be a time role for yoru server"),
                                    days: discord.Option(int, "The number of days before the role expire", min_value=0),
                                    hours : discord.Option(int, "The number of hours days before the role expire (is adding time on top of days)", min_value=0, default=0), 
                                    minutes : discord.Option(int, "The number of minutes days before the role expire (is adding time on top of days and hours)", min_value=0, default=0)):
        await ctx.defer()
        timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        if not self.canTheBotHandleTheRole(ctx, role):
            await ctx.respond("That role {} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
            return
        server = self.data.getServer(ctx.guild.id)
        server.timedRoleOfServer[role.id] = timedelta
        for memberDiscord in ctx.guild.members:
            if role in memberDiscord.roles:
                self.data.addTimedRole(ctx.guild.id, memberDiscord.id, role.id, saveData=False, server=server)
        self.data.saveData()
        embed = discord.Embed(
            title="Server time role added sucessfully !",
            description="The time role {} was added to the timed role of the server with a time delta of {}".format(role.mention, timedelta))
        await ctx.respond(embed=embed)

        
    @slash_command(guild_ids=guildIds, description="Manually add a timed role to a user")            
    @discord.default_permissions(manage_roles=True)
    async def add_timed_role_to_user(self, ctx, member: discord.Option(discord.Member, "The member that will reecive the time role"),
                                    role: discord.Option(discord.Role, "The Role that will be a time role for the member"),
                                    days: discord.Option(int, "The number of days before the role expire", min_value=0),
                                    hours : discord.Option(int, "The number of hours days before the role expire (is adding time on top of days)", min_value=0, default=0), 
                                    minutes : discord.Option(int, "The number of minutes days before the role expire (is adding time on top of days and hours)", min_value=0, default=0)):
        await ctx.defer()
        if not self.canTheBotHandleTheRole(ctx, role):
            await ctx.respond("That role {} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role".format(role.mention))
            return
        timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        memberData = self.data.getMember(member.guild.id, member.id)
        roleIn = False
        pos=0
        for timeRole in memberData.timedRole:
            if timeRole.roleId == role.id:
                roleIn = True
                break
            pos+=1
            
        if not roleIn:
            memberData.timedRole.append(TimedRole(role.id, timedelta))
            await member.add_roles(role)
            embed = discord.Embed(
                title="Custom role delivered sucess !",
                description="The time role {} was deliver to {} with a time delta of {}".format(role.mention, member.mention, timedelta))
            await ctx.respond(embed=embed)
            self.data.saveData()
        else:
            memberData.timedRole[pos].addedTime = datetime.datetime.now()
            memberData.timedRole[pos].timeToKeep = timedelta
            embed = discord.Embed(title="Already have that time role", description="{} already has {} as a time role. The user now have {} left ! (updated the expiration time)".format(member.mention, role.mention, timedelta))
            await ctx.respond(embed=embed)
        
        self.data.saveData()    