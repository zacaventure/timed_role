from discord.ext import commands, tasks
from discord.ext.commands.bot import Bot
from discord.utils import get
from data import Data


class RoleTimeOutChecker(commands.Cog):
    def __init__(self, data: Data, bot: Bot):
        self.data = data
        self.bot = bot
        self.timeChecker.start()

    def cog_unload(self):
        self.timeChecker.cancel()

    @tasks.loop(seconds=60)
    async def timeChecker(self):
        change = False
        for server in self.data.servers:
            for memberItr in server.members:
                timedRoleToRemoves = []
                for timedRole in memberItr.timedRole:
                    if timedRole.isExpire():
                        guild = self.bot.get_guild(server.serverId)
                        if guild is not None:
                            member = guild.get_member(memberItr.memberId)
                            if member is not None:   
                                role_get = get(guild.roles, id=timedRole.roleId)  
                                await member.remove_roles(role_get, reason = "Your role as expired ({} days)".format(timedRole.numberOfDaysToKeep))
                                timedRoleToRemoves.append(timedRole)
                for timeRoleToRemove in timedRoleToRemoves:
                    if timeRoleToRemove in memberItr.timedRole:
                        memberItr.timedRole.remove(timeRoleToRemove)
                        change = True
        if change:
            self.data.saveData()