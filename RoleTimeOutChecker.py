from logging import Logger
import logging
import discord
from discord.ext import commands, tasks
from discord.utils import get
from data import Data
from data_structure.Server import Server


class RoleTimeOutChecker(commands.Cog):
    def __init__(self, data: Data, bot: discord.Bot, logger: Logger):
        self.data = data
        self.bot = bot
        self.logger = logger
        self.timeChecker.start()

    def cog_unload(self):
        self.timeChecker.cancel()

    @tasks.loop(seconds=60)
    async def timeChecker(self):
        change = False
        for server in self.data.servers:
            guild = self.bot.get_guild(server.serverId)
            if guild is not None:
                change = await self.handleIndividualTimedRole(server, guild) or await self.handleGlobalTimedRole(server, guild)  
        if change:
            self.data.saveData()
            
    async def handleIndividualTimedRole(self, server: Server, guild : discord.guild):
        change=False
        for memberItr in server.members:
            timedRoleToRemoves = []
            for timedRole in memberItr.timedRole:
                if timedRole.isExpire():
                    await self.removeRoleToMember(guild, memberItr.memberId, timedRole.roleId)
                    timedRoleToRemoves.append(timedRole)
            for timeRoleToRemove in timedRoleToRemoves:
                if timeRoleToRemove in memberItr.timedRole:
                    memberItr.timedRole.remove(timeRoleToRemove)
                    change = True
        return change
    
    async def handleGlobalTimedRole(self, server: Server, guild : discord.guild):
        change=False
        globalTimedRoleToRemove = []
        for globalTimedRole in server.globalTimeRoles:
            if globalTimedRole.isExpire(server.timezone):
                globalTimedRoleToRemove.append(globalTimedRole)
                for memberDiscord in guild.members:
                    await self.removeRoleToMember(guild, memberDiscord.id, globalTimedRole.roleId)
        for timeRoleToRemove in globalTimedRoleToRemove:
                if timeRoleToRemove in server.globalTimeRoles:
                    server.globalTimeRoles.remove(timeRoleToRemove)
                    change = True  
        return change
        
    async def removeRoleToMember(self, guild: discord.guild, memberId, roleId):
        member: discord.member = guild.get_member(memberId)
        if member is not None:   
            role_get = get(guild.roles, id=roleId)
            if role_get in member.roles:
                try:
                    await member.remove_roles(role_get, reason = "Your role has expired")
                except Exception as error:
                    self.logger.log(logging.ERROR, error)