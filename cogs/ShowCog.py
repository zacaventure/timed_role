import discord
from discord.commands import (  # Importing the decorator that makes slash commands.
    slash_command,
)
from discord.ext import commands
from cogs.Util import get_member_from_id
from constant import guildIds
from data import Data
from data_structure.Server import Server
from discord.utils import get

class ShowCog(commands.Cog):
    def __init__(self, bot, data: Data):
        self.bot = bot
        self.data = data

    @slash_command(guild_ids=guildIds, description="Show all the individual and global timed role of your server")
    async def show_timed_role_of_server(self, ctx):
        await ctx.defer()
        server = self.data.getServer(ctx.guild.id)
        embed = discord.Embed()
        
        value=""
        i = 1
        server.timedRoleOfServer = {k: v for k, v in sorted(server.timedRoleOfServer.items(), key=lambda item: item[1])} # Sort with expiration days
        for roleId, timedelta in server.timedRoleOfServer.items():
            role_get = get(ctx.guild.roles, id=roleId)
            if role_get is not None:
                value += "{}) {} with a time delta of {} \n".format(i, role_get.mention, str(timedelta).split(".")[0])
                i += 1
        if value == "":
            value = "No timed role for your server" 
        embed = discord.Embed(title="Timed role of your server", description=value)
        
        value=""
        i = 1
        server.globalTimeRoles.sort()
        for timeRole in server.globalTimeRoles:
            role_get = get(ctx.guild.roles, id=timeRole.roleId)
            if role_get is not None:
                value += "{}) {} expire on {} \n".format(i, role_get.mention, timeRole.printEndDate())
                i += 1
        if value == "":
            value = "No global timed role for your server" 
        embed2 = discord.Embed(title="Global timed role of your server", description=value)
        embed2.set_footer(text="Note: Global roles expire for everyone in the server at the same time !")
        await ctx.respond(embed=embed)
        await ctx.respond(embed=embed2)
        
    @slash_command(guild_ids=guildIds, description="Show all the individual and global timed role of a member")
    async def show_timed_role_of_member(self, ctx, member: discord.Option(discord.Member, "The member which roles will be show")):
        await ctx.defer()
        server: Server = self.data.getServer(ctx.guild.id)
        embed = discord.Embed()
        
        value=""
        i = 1
        memberData = self.data.getMember(ctx.guild.id, member.id, server=server)
        memberData.timedRole.sort()
        for timeRole in memberData.timedRole:
            role_get = get(ctx.guild.roles, id=timeRole.roleId)
            if role_get is not None:
                value += "{}) {} with {} left\n".format(i, role_get.mention, str(timeRole.getRemainingTimeDelta()).split(".")[0])
                i += 1
        if value == "":
            value = "No timed role for {}".format(member.name) 
        embed = discord.Embed(title="Timed role of {}".format(member.name), description=value)
        
        value=""
        i = 1
        server.globalTimeRoles.sort()
        for timeRole in server.globalTimeRoles:
            role_get = get(ctx.guild.roles, id=timeRole.roleId)
            if role_get in member.roles and role_get is not None:
                value += "{}) {} that expire for everyone on {} \n".format(i, role_get.mention, timeRole.printEndDate())
            i += 1
        if value == "":
            value = "No global timed role for {}".format(member.name) 
        embed2 = discord.Embed(title="Global timed role of {}".format(member.name), description=value)
        await ctx.respond(embed=embed)
        await ctx.respond(embed=embed2)
        
    @slash_command(guild_ids=guildIds, description="Show all the user of a timed role. The time until expire is also shown")
    async def show_timed_role_users(self, ctx: discord.ApplicationContext, 
                                    role: discord.Option(discord.Role, "The common role of the members")):
        await ctx.defer()
        server = self.data.getServer(ctx.guild.id)

        isTimedRoleGlobal=False
        positionGlobalTimedRole=0
        for globalTimedRole in server.globalTimeRoles:
            if globalTimedRole.roleId == role.id:
                isTimedRoleGlobal=True
                break
            positionGlobalTimedRole += 1
        
        members_mentions = {}
        description = ""
        membersTimeDeltaRemain = {}
        memberNoTimedRole = []
        for member in server.members:
            for timeRole in member.timedRole:
                if timeRole.roleId == role.id:
                    member_discord = await get_member_from_id(ctx.guild, member.memberId)
                    if member_discord is not None:
                        membersTimeDeltaRemain[member_discord.id] = timeRole.getRemainingTimeDelta()
                        members_mentions[member_discord.id] = member_discord.mention
                    break
                                
        for memberDiscord in ctx.guild.members:
            if role in memberDiscord.roles:
                if isTimedRoleGlobal:
                    globalTimedRoleTimeDelta = server.globalTimeRoles[positionGlobalTimedRole].getRemainingTimeDelta(server.timezone)
                    if memberDiscord.id not in membersTimeDeltaRemain or globalTimedRoleTimeDelta < membersTimeDeltaRemain[memberDiscord.id]:
                        membersTimeDeltaRemain[memberDiscord.id] = globalTimedRoleTimeDelta
                        members_mentions[memberDiscord.id] = member_discord.mention
                        
                elif not isTimedRoleGlobal and memberDiscord.id not in membersTimeDeltaRemain:
                    memberNoTimedRole.append(memberDiscord)
                    
        membersTimeDeltaRemain = {k: v for k, v in sorted(membersTimeDeltaRemain.items(), key=lambda item: item[1])} # Sort with expiration days 
        for memberId, timedelta in membersTimeDeltaRemain.items():
            description += "{} with {} left \n".format(members_mentions[memberId], str(timedelta).split(".")[0])
        if description == "":
            description = "Nobody have this timed role"
        embed = discord.Embed(
            title="Has the timed role {}".format(role.name),
            description=description
        )
        
        description=""
        i = 1
        for discordMember in memberNoTimedRole:
            description += "{}) {} \n".format(i, discordMember.mention)
            i += 1
        embedNoTimedRole = discord.Embed(
            title="Has the role, but not a timed role for these members".format(role.name),
            description=description
        )
        await ctx.respond(embed=embed)
        if len(memberNoTimedRole) != 0:
            await ctx.respond(embed=embedNoTimedRole)
