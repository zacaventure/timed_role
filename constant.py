import os
from dotenv import load_dotenv
import pytz

# load .env variables
load_dotenv()

guildIds = [833210288681517126] # test discord server
guildIds = None # force global commands


loop_time_check_seconds = 60
MAX_ITEM_PER_PAGES_DEFAULT = 12

datetime_strptime = "%Y-%m-%d %H:%M:%S"

default_database = "time_role.db"
DATABASE = os.getenv("DATABASE_FILE")
if DATABASE is None:
    DATABASE = default_database

default_timezone = "EST"
LOCAL_TIME_ZONE = pytz.timezone(os.getenv("TIMEZONE"))
if LOCAL_TIME_ZONE is None:
    LOCAL_TIME_ZONE = default_timezone

default_backup = "backups/"
BACKUP_DIR = os.getenv("BACKUP_DIR")
if BACKUP_DIR is None:
    BACKUP_DIR = default_backup

TOKEN = os.getenv("TEST_TOKEN")

if TOKEN is None:
    raise Exception("Missing your token, create a .env file with TOKEN = 'your bot token' ")
