import os
from dotenv import load_dotenv
import pytz

# load .env variables
load_dotenv()

# guildIds = [833210288681517126] # test discord server
guildIds = None # force global commands


loop_time_check_seconds = 60
MAX_ITEM_PER_PAGES_DEFAULT = 12

# defaults
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////
datetime_strptime = "%Y-%m-%d %H:%M:%S"
default_database = os.path.join(os.path.dirname(os.path.realpath(__file__)), "time_role.db")
default_timezone = "EST"
default_backup = os.path.join(os.path.dirname(os.path.realpath(__file__)), "backups")
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////

LOG_DIR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")
if not os.path.exists(LOG_DIR_PATH):
    os.makedirs(LOG_DIR_PATH)

DATABASE = os.getenv("DATABASE_FILE")
if DATABASE is None:
    DATABASE = default_database

LOCAL_TIME_ZONE = pytz.timezone(os.getenv("TIMEZONE"))
if LOCAL_TIME_ZONE is None:
    LOCAL_TIME_ZONE = default_timezone

BACKUP_DIR = os.getenv("BACKUP_DIR")
if BACKUP_DIR is None:
    BACKUP_DIR = default_backup

TOKEN = os.getenv("TOKEN")

if TOKEN is None:
    raise Exception("Missing your token, create a .env file with TOKEN = 'your bot token' ")
