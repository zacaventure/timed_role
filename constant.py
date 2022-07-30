import os
from dotenv import load_dotenv

# load .env variables
load_dotenv()

# guildIds = [833210288681517126] # test discord server
guildIds = None # force global commands


loop_time_check_seconds = 60
MAX_ITEM_PER_PAGES_DEFAULT = 10

BACKUP_DIR = os.getenv("BACKUP_DIR")
TOKEN = os.getenv("TOKEN")
