from __future__ import annotations
from logging import getLogger, INFO
from typing import TYPE_CHECKING

from discord import Member, Role
from aiohttp.client_exceptions import ClientConnectorError
if TYPE_CHECKING:
    from timeRoleBot import TimeRoleBot
    from database.database import Database
import datetime
import math
from discord.ext import commands, tasks
from cogs.Util import is_connected_to_internet
from constant import loop_time_check_seconds, datetime_strptime

class RoleTimeOutChecker(commands.Cog):
    def __init__(self, bot: TimeRoleBot):
        self.bot: TimeRoleBot = bot
        self.database: Database = self.bot.database
        self.logger = getLogger("discord_time_checker")
        
        self.isLooping = False
        self.longestTimedelta = datetime.timedelta(days=-1)

    def cog_unload(self):
        self.timeChecker.cancel()
        
        
    def start(self):
        self.timeChecker.start()

    async def delete_role_from_guild(self, guild_id: int, role_id: int, reason: str) -> tuple[int, int] | None:
        guild, network_error = await self.bot.get_or_fetch_guild(guild_id)
        if network_error:
            return None
        if guild is not None:
            role, network_error = await self.bot.get_or_fetch_role(guild, role_id)
            if network_error:
                return None
            if role is not None:
                await role.delete(reason=reason)
        return (guild_id, role_id)
    
    """
    async def delete_role_from_guild_to_members(self, guild_id: int, member_id: int, role_id: int, reason: str) -> tuple[int, int] | None:
        guild, network_error = await self.bot.get_or_fetch_guild(guild_id)
        if network_error:
            return None
        if guild is not None:
            role, network_error = await self.bot.get_or_fetch_role(guild, role_id)
            if network_error:
                return None
            if role is not None:
                await role.delete(reason=reason)
        return (guild_id, role_id)
    """
        
    async def remove_role_to_members(self, members: list[Member], role: Role) -> bool:
        connection_error = False
        nb_consecutive_network_errors = 0
        for member in members:
            try:
                await member.remove_roles(role, reason = f"The recurrent role {role} is expiring")
                nb_consecutive_network_errors = 0
            except ClientConnectorError:
                connection_error = True
                nb_consecutive_network_errors += 1
                if nb_consecutive_network_errors > 5:
                    return True
                continue
            except Exception as e:
                self.logger.exception(f"\n On member {member} with roles {member.roles}.\n To delete role {role} with id {role.id}.\n In server {member.guild}, with roles {member.guild.roles}\n")
    
        return connection_error
    async def handle_expired_recurrent_roles(self) -> None:
        recurrent_roles_to_update_in_database = []
        async for guild_id, role_id, next_datetime, deltatime, now in self.database.get_all_expired_recurrent_roles():
            guild, network_error = await self.bot.get_or_fetch_guild(guild_id)
            if network_error:
                continue
            if guild is not None:
                role, network_error = await self.bot.get_or_fetch_role(guild, role_id)
                if network_error:
                    continue
            if guild is not None and role is not None:
                had_connection_errors = await self.remove_role_to_members(role.members, role)
                if had_connection_errors:
                    continue

            next_datetime_new = datetime.datetime.strptime(next_datetime, datetime_strptime)
            seconds = now.timestamp() - next_datetime_new.timestamp()
            factor = math.ceil(seconds / deltatime.total_seconds())
            next_datetime_new = next_datetime_new + (factor * deltatime)
            recurrent_roles_to_update_in_database.append((next_datetime_new.strftime(datetime_strptime), role_id, guild_id))
        await self.database.update_next_datetime_recurrent_roles(recurrent_roles_to_update_in_database)


    @tasks.loop(seconds=loop_time_check_seconds)
    async def timeChecker(self):
        if not self.isLooping and await is_connected_to_internet():
            self.isLooping = True
            start = datetime.datetime.now()
            try:
                await self.database.remove_expired_time_role(self.bot, self.logger)
                await self.database.remove_expired_global_time_role(self.bot, self.logger)
                await self.handle_expired_recurrent_roles()
                await self.database.commit()
            except Exception as error:
                self.logger.exception("Exception while running time checker. Excepton {}".format(error))
            delta = datetime.datetime.now() - start
            if delta > self.longestTimedelta:
                self.logger.log(INFO, "New longest loop: {}".format(delta))
                self.longestTimedelta = delta
            self.isLooping = False