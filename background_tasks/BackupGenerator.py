from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database.database import Database

import datetime
import os
from discord.ext import commands, tasks
from constant import BACKUP_DIR

class BackupGenerator(commands.Cog):
    def __init__(self, database: Database):
        self.database = database
        self.max_backup = 40
        self.logger = getLogger("discord_backups")

    def cog_unload(self) -> None:
        self.backup_loop.cancel()
        
        
    def start(self) -> None:
        self.backup_loop.start()
        
    def remove_pass_backups(self) -> int:
        files = os.listdir(BACKUP_DIR)
        nb = len(files)
        
        if nb > self.max_backup:
            files.sort(reverse=False)
            nb = len(files)
            
            i = 0
            while nb > self.max_backup:
                os.remove(os.path.join(BACKUP_DIR, files[i]))
                nb -= 1
                i += 1
            return self.max_backup
        
        return nb
        
    async def backup_now(self, additional_info: str = "") -> None:
        if os.path.isdir(BACKUP_DIR):
            now = datetime.datetime.now()
            nb_backups = self.remove_pass_backups()
            
            backup_file_path = os.path.join(BACKUP_DIR, now.strftime("%Y_%m_%d-%H_%M_%S") + additional_info + ".db")
            await self.database.backup(backup_file_path)
            
            self.logger.info("The database got backup at {} with now {} backups".format(backup_file_path, nb_backups))
        else:
            self.logger.error("The dir {} does not exist".format(BACKUP_DIR))

    @tasks.loop(hours=12)
    async def backup_loop(self) -> None:
        await self.backup_now()