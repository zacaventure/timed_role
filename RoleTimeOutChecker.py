from discord.ext import commands, tasks
import datetime
import pytz


class RoleTimeOutChecker(commands.Cog):
    def __init__(self, data):
        self.data = data
        self.timeChecker.start()

    def cog_unload(self):
        self.timeChecker.cancel()

    @tasks.loop(seconds=60)
    async def timeChecker(self):
        now = datetime.datetime.now()