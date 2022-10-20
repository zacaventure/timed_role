import datetime
import logging
import os
from discord.ext import commands, tasks
from constant import BACKUP_DIR
import database.database as database

logger = logging.getLogger("discord_backups")
logger.setLevel(logging.INFO)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "backups.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(message)s'))
logger.addHandler(handler)

class BackupGenerator(commands.Cog):
    def __init__(self):
        self.max_backup = 100

    def cog_unload(self):
        self.backup_loop.cancel()
        
        
    def start(self):
        self.backup_loop.start()
        
    async def backup_now(self, additional_info: str = ""):
        if os.path.isdir(BACKUP_DIR):
            now = datetime.datetime.now()
            files = os.listdir(BACKUP_DIR)
            if len(files) > self.max_backup:
                files.sort(reverse=False)
                os.remove(os.path.join(BACKUP_DIR, files[0]))
            backup_file_path = os.path.join(BACKUP_DIR, now.strftime("%Y_%m_%d-%H_%M_%S") + additional_info + ".db")
            await database.backup(backup_file_path)
            logger.info("The database got backup at {} with now {} backups".format(backup_file_path, len(files)))
        else:
            logger.error("The dir {} does not exist".format(BACKUP_DIR))

    @tasks.loop(hours=5)
    async def backup_loop(self):
        await self.backup_now()