import logging
import os
import aiohttp
import discord


import discord

MAX_NUMBER_OF_RETRIES = 10

logger = logging.getLogger("discord_utils")
logger.setLevel(logging.INFO)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..","logs", "utils.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

async def get_member_from_id(guild: discord.Guild, memberId: int) -> discord.Member:
    global logger
    member: discord.Member = None
    retries_nb = 0
    while True:
        try:
            member = guild.get_member(memberId)
            if member is None:
                member = await guild.fetch_member(memberId)
            return member
        except discord.errors.NotFound:
            # member no longer exist in that guild
            return None
        except aiohttp.client_exceptions.ClientConnectorError:
            retries_nb += 1
        except Exception:
            logger.exception("Unkown exception on with guild {} and memberId: {}".format(guild, memberId))
        if retries_nb >= MAX_NUMBER_OF_RETRIES:
            return member
        
sites = [
    "https://www.google.com/",
    "https://www.amazon.ca/-/fr/",
    "https://www.facebook.com/"
]
        
async def is_connected_to_internet():
    async with aiohttp.ClientSession() as session:
        for site in sites:
            try:
                async with session.head(site) as response:
                    return True
            except Exception as e:
                pass
        logger.error("NOT CONNECTED TO INTERNET.....")
        return False