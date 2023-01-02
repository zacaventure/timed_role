from __future__ import annotations
from logging import getLogger, INFO
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from timeRoleBot import TimeRoleBot
    from database.database import Database
    
import datetime
from discord.ext import commands, tasks
from cogs.Util import is_connected_to_internet
from constant import loop_time_check_seconds


class RoleTimeOutChecker(commands.Cog):
    def __init__(self, bot: TimeRoleBot):
        self.bot: TimeRoleBot = bot
        self.database: Database = self.bot.database
        self.logger = getLogger("discord_time_checker")
        
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
                await self.database.remove_expired_time_role(self.bot, self.logger)
                await self.database.remove_expired_global_time_role(self.bot, self.logger)
                await self.database.commit()
            except Exception as error:
                self.logger.error("Exception while running time checker. Excepton {}".format(error))
            delta = datetime.datetime.now() - start
            if delta > self.longestTimedelta:
                self.logger.log(INFO, "New longest loop: {}".format(delta))
                self.longestTimedelta = delta
            self.isLooping = False