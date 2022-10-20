import datetime
import logging
import os
import database.database as database
from discord.ext.commands import Bot
from discord.ext import commands, tasks
from cogs.Util import is_connected_to_internet
from constant import loop_time_check_seconds


class RoleTimeOutChecker(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.logger = logging.getLogger("discord_time_checker")
        self.logger.setLevel(logging.INFO)
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "time_checker.log")
        handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
        handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
        self.logger.addHandler(handler)
        
        self.isLooping = False
        self.longestTimedelta = datetime.timedelta(days=-1)

    def cog_unload(self):
        self.timeChecker.cancel()
        
        
    def start(self):
        self.timeChecker.start()

    @tasks.loop(seconds=loop_time_check_seconds)
    async def timeChecker(self):
        if not self.isLooping and await is_connected_to_internet():
            self.isLooping = True
            start = datetime.datetime.now()
            try:
                await database.remove_expired_time_role(self.bot, self.logger)
                await database.remove_expired_global_time_role(self.bot, self.logger)
            except Exception as error:
                self.logger.log(logging.ERROR, "Exception while running time checker. Excepton {}".format(error))
            delta = datetime.datetime.now()-start
            if delta > self.longestTimedelta:
                self.logger.log(logging.INFO, "New longest loop: {}".format(delta))
                self.longestTimedelta = delta
            self.isLooping = False