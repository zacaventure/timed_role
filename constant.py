import os
from dotenv import load_dotenv
import pytz

# load .env variables
load_dotenv()

TESTING = False

# help server
ADMIN_COMMANDS_SERVER = [937141485822951445]
if TESTING:
    ADMIN_COMMANDS_SERVER = None

guildIds = [833210288681517126] # test discord server
if not TESTING:
    guildIds = None # force global commands


MAX_ITEM_PER_PAGES_DEFAULT = 10

# defaults
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////
datetime_strptime = "%Y-%m-%d %H:%M:%S"
default_database = os.path.join(os.path.dirname(os.path.realpath(__file__)), "time_role.db")
default_timezone = "EST"
default_backup = os.path.join(os.path.dirname(os.path.realpath(__file__)), "backups")
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////
RES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "res")

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
if TESTING:
    TOKEN = os.getenv("TEST_TOKEN")

SUPPORT_SERVER_INVITE_URL = "https://discord.gg/hRTHpB4HUC"

if TOKEN is None:
    raise Exception("Missing your token, create a .env file with TOKEN = 'your bot token' ")
