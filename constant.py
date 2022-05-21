import os
from dotenv import load_dotenv

# load .env variables
load_dotenv()

# guildIds = [833210288681517126] # test discord server
guildIds = None # force global commands

TOKEN = os.getenv("TOKEN")
