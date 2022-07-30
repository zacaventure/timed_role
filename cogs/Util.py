import logging
import os
import aiohttp
import discord
from discord.ext import pages


import discord

from constant import MAX_ITEM_PER_PAGES_DEFAULT

MAX_NUMBER_OF_RETRIES = 10

logger = logging.getLogger("discord_utils")
logger.setLevel(logging.INFO)
file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..","logs", "utils.log")
handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def generate_pages(item_list, max_number_of_item_per_page, titles: str = "", footers: str = ""):
    pageList = []
    realCount = 1
    count = 1
    embedText = ""
    for item_str in item_list:
        if count <= max_number_of_item_per_page:
            embedText += item_str + "\n"
        if count >= max_number_of_item_per_page or realCount == len(item_list):
            embed = discord.Embed(description=embedText, title=titles)
            embed.set_footer(text=footers)
            pageList.append(pages.Page(
                embeds=[
                    embed
                ],
            ))
            count = 0
            embedText = ""
        count += 1
        realCount += 1
    return pageList

def get_paginator(text: str, titles: str = "", footers: str = "", max_number_of_item_per_page=MAX_ITEM_PER_PAGES_DEFAULT):
    return pages.Paginator(pages=generate_pages(text.strip().split("\n"),
                                                max_number_of_item_per_page, 
                                                titles=titles, footers=footers))     

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