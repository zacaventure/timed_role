import datetime
import logging
import os
from discord.ext import commands, tasks
from constant import BACKUP_DIR
from data import Data

logger = logging.getLogger("discord_backups")
logger.setLevel(logging.ERROR)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "backups.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class BackupGenerator(commands.Cog):
    def __init__(self, data: Data):
        self.data = data
        self.max_backup = 720

    def cog_unload(self):
        self.backup_loop.cancel()
        
        
    def start(self):
        self.backup_loop.start()
        
    def backup_now(self, additional_info: str = ""):
        if os.path.isdir(BACKUP_DIR):
            now = datetime.datetime.now()
            files = os.listdir(BACKUP_DIR)
            if len(files) > self.max_backup:
                files.sort(reverse=False)
                os.remove(os.path.join(BACKUP_DIR, files[0]))
            self.data.saveData(file=os.path.join(BACKUP_DIR, now.strftime("%Y_%m_%d-%H_%M_%S") + additional_info + ".bin" ))
        else:
            logger.error("The dir {} does not exist".format(BACKUP_DIR))

    @tasks.loop(hours=1)
    async def backup_loop(self):
        self.backup_now()