import datetime
import logging
import os
import random
import discord
from discord.ext import commands, tasks
from RetryInfo import RetryInfo
from data import Data
from data_structure.Server import Server


class RoleTimeOutChecker(commands.Cog):
    def __init__(self, data: Data, bot: discord.Bot):
        self.data = data
        self.bot: discord.Bot = bot
        self.logger = logging.getLogger("discord_time_checker")
        self.logger.setLevel(logging.INFO)
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "time_checker.log")
        handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
        handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
        self.logger.addHandler(handler)
        
        self.isLooping = False
        self.deleteRoleRetry = {}
        self.MAX_NUMBER_OF_RETRY = 8
        self.longestTimedelta = datetime.timedelta(days=-1)

    def cog_unload(self):
        self.timeChecker.cancel()
        
        
    def start(self):
        self.timeChecker.start()
        
    async def retryFailConnection(self):
        if len(self.deleteRoleRetry) != 0:
            toRemove = []
            for retryInfo in self.deleteRoleRetry.keys():
                toRemove.append(retryInfo)
            for retryInfo in toRemove:
                await self.removeRoleToMember(retryInfo.guild, retryInfo.memberId, retryInfo.roleId)
        
    def handleError(self, error : Exception, guild: discord.Guild, memberId, roleId):
        if "Cannot connect to host discord.com" in str(error):
            retryInfo = RetryInfo(guild, memberId, roleId)
            if retryInfo in self.deleteRoleRetry:
                self.deleteRoleRetry[retryInfo] += 1
                if self.deleteRoleRetry[retryInfo] > self.MAX_NUMBER_OF_RETRY:
                    del self.deleteRoleRetry[retryInfo]
                    self.logger.log(logging.ERROR, "{} \n On member id {} and roleid {} after {} try".format(error,
                                                                                                             memberId, 
                                                                                                             roleId, 
                                                                                                             self.MAX_NUMBER_OF_RETRY))
            else:
                self.deleteRoleRetry[retryInfo] = 0
            return False
        return True

    @tasks.loop(seconds=15)
    async def timeChecker(self):
        if not self.isLooping:
            self.isLooping = True
            start = datetime.datetime.now()
            try:
                change = False
                change = change or await self.retryFailConnection()
                for server in self.data.servers:
                    guild = self.bot.get_guild(server.serverId)
                    if guild is None:
                        try:
                            guild = await self.bot.fetch_guild(server.serverId)
                        except Exception:
                            guild = None
                    if guild is not None:
                        change = await self.handleIndividualTimedRole(server, guild) or await self.handleGlobalTimedRole(server, guild)  
                change = change or await self.retryFailConnection()
                if change:
                    self.data.saveData()
            except Exception as error:
                self.logger.log(logging.ERROR, "Exception while running time checker. Excepton {}".format(error))
            delta = datetime.datetime.now()-start
            if delta > self.longestTimedelta:
                self.logger.log(logging.INFO, "New longest loop: {}".format(delta))
                self.longestTimedelta = delta
            self.isLooping = False
            
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
        
    async def removeRoleToMember(self, guild: discord.Guild, memberId, roleId):
        member: discord.Member = guild.get_member(memberId)
        if member is None:
            try:
                member: discord.Member = await guild.fetch_member(memberId)
            except Exception as e:
                member = None
                self.handleError(e, guild, memberId, roleId)
        role_get: discord.Role = guild.get_role(roleId)
        if role_get is None:
            try:
                role_get: discord.Role = await guild._fetch_role(roleId)
            except Exception as e2:
                self.handleError(e2, guild, memberId, roleId)
                role_get = None 
        if member is not None and role_get is not None:   
            if role_get in member.roles:
                try:
                    await member.remove_roles(role_get, reason = "Your role has expired")
                    retryInfo = RetryInfo(guild, memberId, roleId)
                    if retryInfo in self.deleteRoleRetry:
                        del self.deleteRoleRetry[retryInfo]
                except Exception as error:
                    if self.handleError(error, guild, memberId, roleId):
                        self.logger.exception("\n On member {}  with roles {}.\n To delete role {} with id {}.\n In server {}, with roles {}\n"
                                    .format(member, member.roles, role_get, role_get.id, guild, guild.roles))
        else:
            if member is None:
                self.logger.log(logging.ERROR, "NONE Member")
            elif role_get is None:
                self.logger.log(logging.ERROR, "NONE role")
            if member is None and role_get is None:
                self.logger.log(logging.ERROR, "NONE Member and role")