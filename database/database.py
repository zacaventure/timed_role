
from __future__ import annotations
import asyncio
from multiprocessing import Pool
from multiprocessing.pool import AsyncResult
from typing import TYPE_CHECKING, AsyncGenerator, Generator

from datetime import datetime, timedelta
from constant import datetime_strptime
import aiosqlite
import os
import pytz
import aiohttp
import sqlite3
import logging
from constant import DATABASE

if TYPE_CHECKING:
    from timeRoleBot import TimeRoleBot

class Database:
    
    def __init__(self) -> None:
        self.connection: aiosqlite.Connection = None
        self.logger = logging.getLogger("start")
        
    async def connect(self) -> None:
        if self.connection is None:
            self.connection = await aiosqlite.connect(DATABASE)
            await self.activate_wal_mode()
            
    async def activate_wal_mode(self) -> None:
        activate_str = "PRAGMA journal_mode=WAL";
        async with self.connection.cursor() as cursor:
            result = await cursor.execute(activate_str)
            result = (await result.fetchone())[0]
            if result != "wal":
                logging.getLogger("start").error("Could not activate wal mode")
                raise Exception("Could not activate wal mode")
        
    async def create_database_if_not_exist(self) -> None:
        database_str = None
        database_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "create_database.sql")
        with open(database_path, "r") as file:
            database_str = file.read()
            await self.connection.executescript(database_str)
            await self.connection.commit()
            
    async def drop_database(self):
        drop = """
        DROP TABLE IF EXISTS Guild;
        DROP TABLE IF EXISTS Member;
        DROP TABLE IF EXISTS Member_time_role;
        DROP TABLE IF EXISTS Time_role;
        DROP TABLE IF EXISTS Global_time_role;"""
        await self.connection.executescript(drop)
        await self.connection.commit()
        
    async def insert_if_not_exist_guild(self, id: int, timezone: str | None = None, commit=False):
        result = await self.connection.execute("SELECT EXISTS(SELECT 1 FROM Guild WHERE id=?);", (id,))
        is_guild_in_database = (await result.fetchone())[0]
        if not is_guild_in_database:
            insert_guild_querry = "INSERT INTO Guild (id, timezone) VALUES(?, ?);"
            await self.connection.execute(insert_guild_querry, (id, timezone))
            if commit:
                await self.connection.commit()
                
    async def _get_first_in_database(self, querry: str, data=None) ->  aiosqlite.Row:
        async with self.connection.execute(querry, data) as cursor:
            result = await cursor.fetchone()
            if result is None:
                return None
            else:
                return result
    
    async def insert_member_time_role(self, role_id: int, deltatime: timedelta, 
                                    member_id: int, guild_id: int, creation_time: datetime=None) -> None:
        
        insert_member_time_role_querry = """
        INSERT OR IGNORE INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
        VALUES (?, ?, ?, ?, ?) ;"""
        
        if creation_time is None:
            creation_time = datetime.now()
        await self.connection.execute(insert_member_time_role_querry, 
                (role_id, creation_time.strftime(datetime_strptime), deltatime.total_seconds(), member_id, guild_id)
        )
        
    async def insert_all_member_time_role(self, member_time_role_list) -> None:
        
        insert_member_time_role_querry = """
        INSERT OR IGNORE INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
        VALUES (?, ?, ?, ?, ?) ;"""
        
        await self.connection.executemany(insert_member_time_role_querry, member_time_role_list)
        
    async def insert_or_update_member_time_role(self, role_id: int, deltatime: timedelta, 
                                    member_id: int, guild_id: int) -> float:
        
        insert_member_time_role_querry = """
        INSERT INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
        VALUES (?, ?, ?, ?, ?) ;"""
        insert_data = (role_id, datetime.now().strftime(datetime_strptime), 
                                    deltatime.total_seconds(), member_id, guild_id)
        
        update_member_time_role_querry = """
        UPDATE Member_time_role
        SET deltatime = ?, creation_time = ?
        WHERE id = ? AND member_id = ? AND  guild_id = ?;"""
        
        select = """
        SELECT 	deltatime, creation_time
        FROM Member_time_role
        WHERE id = ? AND member_id = ? AND  guild_id = ? ;
        """
        select_data = (role_id, member_id, guild_id)
        
        member_time_role = await self._get_first_in_database(select, select_data)
        if member_time_role is None:
            await self.connection.execute(insert_member_time_role_querry, insert_data)
            return None
        else:
            update_data = (deltatime.total_seconds(), 
                        datetime.now().strftime(datetime_strptime), role_id, member_id, guild_id)
            await self.connection.execute(update_member_time_role_querry, update_data)
            return member_time_role[0]
            
                  
    async def get_member_time_role(self, member_id: int, guild_id: int):
        select = """
        SELECT 	id, creation_time, deltatime
        FROM Member_time_role
        WHERE ( member_id = ? AND guild_id = ?) ;
        """
        async with self.connection.execute(select, (member_id, guild_id)) as cursor:
            results = await cursor.fetchall()
            return results
            
    async def get_member_time_role_from_guild(self, role_id: int, guild_id: int):
        select = """
        SELECT 	creation_time, deltatime, member_id
        FROM Member_time_role
        WHERE ( id = ? AND guild_id = ?) ;
        """
        return await self.connection.execute_fetchall(select, (role_id, guild_id))

    async def get_time_role_deltatime(self, role_id: int, guild_id: int) -> timedelta | None:
        select = """
        SELECT deltatime
        FROM
            Time_role
        WHERE ( id = ? AND guild_id = ?) ;
        """
        async with self.connection.execute(select, (role_id, guild_id)) as cursor:
            result = await cursor.fetchone()
            if result is None:
                return None
            else:
                return timedelta(seconds=result[0])
            
    def get_time_role_deltatime_sync(self, connection: sqlite3.Connection, role_id: int, guild_id: int) -> timedelta | None:
        select = """
        SELECT deltatime
        FROM
            Time_role
        WHERE ( id = ? AND guild_id = ?) ;
        """
        result = connection.execute(select, (role_id, guild_id)).fetchone()
        if result is None:
            return None
        else:
            return timedelta(seconds=result[0])
            
    async def get_all_server_time_roles(self, guild_id: int):
        select = """
        SELECT id, deltatime
        FROM 
            Time_role
        WHERE guild_id = ? ;
        """
        return await self.connection.execute_fetchall(select, (guild_id,))
                
    async def insert_or_update_time_role(self, role_id: int, deltatime: timedelta, guild_id: int) -> timedelta | None:
        await self.insert_if_not_exist_guild(guild_id, None)
        insert_time_role_querry = """
        INSERT INTO Time_role (id, guild_id, deltatime)
        VALUES(?, ?, ?);
        """
        
        update_time_role_querry = """
        UPDATE Time_role
        SET deltatime = ?
        WHERE id = ? AND guild_id = ? ;"""
        
        previous_deltime = await self.get_time_role_deltatime(role_id, guild_id)
        if previous_deltime is not None:
            await self.connection.execute(update_time_role_querry, (deltatime.total_seconds(), role_id, guild_id))
        else:
            await self.connection.execute(insert_time_role_querry, (role_id, guild_id, deltatime.total_seconds()))
        return previous_deltime


    async def get_global_time_role(self, role_id: int, guild_id: int):
        select = """
        SELECT *
        FROM
            Global_time_role
        WHERE ( id = ? AND guild_id = ?) ;
        """
        return await self._get_first_in_database(select, (role_id, guild_id))

    async def get_recurrent_time_role(self, role_id: int, guild_id: int):
        select = """
        SELECT *
        FROM
            Recurrent_time_role
        WHERE ( id = ? AND guild_id = ?) ;
        """
        return await self._get_first_in_database(select, (role_id, guild_id))
    
    async def get_recurrent_time_roles_of_server(self, guild_id: int) -> list[tuple[int, str, int]]:
        select = """
        SELECT id, next_datetime, deltatime
        FROM
            Recurrent_time_role
        WHERE guild_id = ?;
        """
        async with self.connection.execute(select, (guild_id,)) as cursor:
            return await cursor.fetchall()
        
    async def get_all_recurrent_time_roles(self, guild_id: int) -> list[tuple]:
        select = """
        SELECT *
        FROM
            Recurrent_time_role
        WHERE guild_id = ?;
        """
        async with self.connection.execute(select, (guild_id,)) as cursor:
            return await cursor.fetchall()
    
    async def insert_or_update_global_time_role(self, role_id: int, end_datetime: datetime,
                                      guild_id: int, delete_from_guild: bool) -> str | None:
        await self.insert_if_not_exist_guild(guild_id, None)
        insert_time_role_querry = """
        INSERT INTO Global_time_role (id, end_datetime, guild_id, delete_from_guild)
        VALUES(?, ?, ?, ?);
        """
        
        update_time_role_querry = """
        UPDATE Global_time_role
        SET end_datetime = ?
        WHERE id = ? AND guild_id = ? ;"""
        
        global_time_role = await self.get_global_time_role(role_id, guild_id)
        if global_time_role is not None:
            await self.connection.execute(update_time_role_querry, (end_datetime.strftime(datetime_strptime), role_id, guild_id))
            return global_time_role[1]
        else:
            await self.connection.execute(insert_time_role_querry, 
                    (role_id, end_datetime.strftime(datetime_strptime), guild_id, delete_from_guild))
            return None

    async def insert_or_update_recurring_time_role(self, role_id: int, guild_id: int, 
                        start_datetime: datetime, deltatime: timedelta) -> str | None:
        await self.insert_if_not_exist_guild(guild_id, None)

        insert_querry = """
        INSERT INTO Recurrent_time_role (id, guild_id, start_datetime, next_datetime, deltatime)
        VALUES(?, ?, ?, ?, ?);
        """
        
        update_time_role = """
        UPDATE Recurrent_time_role
        SET start_datetime = ?, next_datetime = ?, deltatime = ?
        WHERE id = ? AND guild_id = ? ;"""
        
        recurrent_time_role = await self.get_recurrent_time_role(role_id, guild_id)
        next_datetime = self.calculate_next_datetime_recurrent_time_role(
            start_datetime, deltatime, None if recurrent_time_role is None else recurrent_time_role[3]
        )
        next_datetime_str = next_datetime.strftime(datetime_strptime)
        start_datetime_str = start_datetime.strftime(datetime_strptime)
        if recurrent_time_role is not None:
            await self.connection.execute(update_time_role, (start_datetime_str, next_datetime_str, deltatime.total_seconds(), role_id, guild_id))
            return (False, next_datetime)
        else:
            await self.connection.execute(insert_querry, 
                    (role_id, guild_id, start_datetime_str, next_datetime_str, deltatime.total_seconds()))
            return (True, start_datetime_str, next_datetime_str, deltatime)
    
    def calculate_next_datetime_recurrent_time_role(self, start_datetime: datetime, deltatime: timedelta,
            next_datetime: datetime) -> datetime:
        if next_datetime is None:
            return start_datetime
        else:
            return next_datetime + deltatime
        
    async def get_all_global_time_roles(self, guild_id: int):
        select = """
        SELECT id, end_datetime
        FROM
            Global_time_role
        WHERE ( guild_id = ?) ;
        """
        return await self.connection.execute_fetchall(select, (guild_id,))
    
    async def get_timezone(self, guild_id: int) -> str:
        select = """
        SELECT timezone
        FROM
            Guild
        WHERE ( id = ?) ;
        """
        timezone = await self._get_first_in_database(select, (guild_id,))
        if timezone is None:
            return timezone
        return timezone[0]
        
    async def insert_or_update_timezone(self, timezone: str, guild_id: int) -> str:
        await self.insert_if_not_exist_guild(guild_id)
        old_timezone = await self.get_timezone(guild_id)
        
        if old_timezone == timezone:
            return old_timezone
        
        update_timezone_querry = """
        UPDATE Guild
        SET timezone = ?
        WHERE id = ? ;"""
        await self.connection.execute(update_timezone_querry, (timezone, guild_id))
        return old_timezone
    
    async def _is_in_database(self, querry: str, data=None) -> bool:
        result = await self.connection.execute(querry, data)
        return bool((await result.fetchone())[0])
    
    def _is_in_database_sync(self, connection: sqlite3.Connection, querry: str, data=None) -> bool:
        result = connection.execute(querry, data)
        return bool((result.fetchone())[0])
    
    async def is_guild_in_database(self, guild_id: int):
        exist_guild_querry = """
        SELECT EXISTS(SELECT 1 FROM Guild WHERE id=? LIMIT 1);
        """
        return await self._is_in_database(exist_guild_querry, data=(guild_id,) )

    async def is_global_time_role_in_database(self, role_id: int, guild_id: int):
        exist_time_role_querry = """
        SELECT EXISTS(SELECT 1 FROM Global_time_role WHERE(id=? AND guild_id=?) LIMIT 1);
        """
        return await self._is_in_database(exist_time_role_querry, data=(role_id, guild_id))

    async def is_member_time_role_in_database(self, role_id: int, member_id: int, guild_id: int):
        exist_member_time_role_querry = """
        SELECT EXISTS(SELECT 1 FROM Member_time_role WHERE(id=? AND member_id=? AND guild_id=?) LIMIT 1);
        """
        return await self._is_in_database(exist_member_time_role_querry, data=(role_id, member_id, guild_id))
    
    def is_member_time_role_in_database_sync(self, connection: sqlite3.Connection, role_id: int, member_id: int, guild_id: int):
        exist_member_time_role_querry = """
        SELECT EXISTS(SELECT 1 FROM Member_time_role WHERE(id=? AND member_id=? AND guild_id=?) LIMIT 1);
        """
        return self._is_in_database_sync(connection, exist_member_time_role_querry, data=(role_id, member_id, guild_id))

    async def is_time_role_in_database(self, role_id: int, guild_id: int):
        exist_time_role_querry = """
        SELECT EXISTS(SELECT 1 FROM Time_role WHERE(id=? AND guild_id=?) LIMIT 1);
        """
        return await self._is_in_database(exist_time_role_querry, (role_id, guild_id))
    
    async def remove_expired_time_role(self, bot: TimeRoleBot, logger=None):
        to_delete_roles = []
        select = """
        SELECT 	*
        FROM Member_time_role ;
        """
        async with self.connection.execute(select) as cursor:
            async for row in cursor:
                now = datetime.now()
                deltatime = timedelta(seconds=row[2])
                creation_datetime = datetime.strptime(row[1], datetime_strptime)
                if now - creation_datetime > deltatime:
                    
                    guild, member, role, network_error = await bot.get_or_fetch_guild_member_role(
                        row[4], row[3], row[0])
                    if member is not None and role is not None and guild is not None:
                        try:
                            if role in member.roles:
                                # the time role will be deleted in the database with on_member_update event
                                await member.remove_roles(role, reason = "Your role has expired after {}".format(deltatime))
                            else:
                                # the member dont have the role anymore
                                to_delete_roles.append((row[0], row[3], row[4]))
                        except aiohttp.client_exceptions.ClientConnectorError:  # type: ignore
                            # network error, will retry to delete it next iteration
                            pass
                        except Exception as e:
                            if logger is not None:
                                logger.exception("\n On member {}  with roles {}.\n To delete role {} with id {}.\n In server {}, with roles {}\n"
                                .format(member, member.roles, role, role.id, guild, guild.roles))
                            to_delete_roles.append((row[0], row[3], row[4]))
                    elif not network_error:
                        to_delete_roles.append((row[0], row[3], row[4]))
                        
        if len(to_delete_roles) > 0 :                     
            remove_member_time_role_querry = """
            DELETE FROM Member_time_role
            WHERE(id=? AND member_id=? AND guild_id=?)
            """
            await self.connection.executemany(remove_member_time_role_querry, to_delete_roles)
            
    async def remove_expired_global_time_role(self, bot: TimeRoleBot, logger=None):
        select = """
        SELECT g.id, g.timezone, t.id, t.end_datetime, t.delete_from_guild
        FROM Guild as g INNER JOIN Global_time_role as t
        ON g.id = t.guild_id ;
        """
        to_delete_roles = []
        async with self.connection.execute(select) as cursor:
            async for row in cursor:
                if row[1] is None:
                    now = datetime.now()
                else:
                    now = datetime.now(tz=pytz.timezone(row[1]))
                if now.strftime(datetime_strptime) > row[3]:
                    guild, network_error = await bot.get_or_fetch_guild(row[0])
                    if guild is not None:
                        role, network_error2 = await bot.get_or_fetch_role(guild, row[2])
                        if role is not None:
                            if row[4] == 1:
                                try:
                                    # the time role will be deleted in the database with on_guild_role_delete event
                                    await role.delete(reason="The global time role as expire on {}".format(row[3]))
                                except aiohttp.client_exceptions.ClientConnectorError:  # type: ignore
                                    pass
                                except Exception as e:
                                    if logger is not None:
                                        logger.exception("\n To delete role {} with id {}.\n In Guild {}, with roles {}\n"
                                        .format(role, role.id, guild, guild.roles))
                                    to_delete_roles.append((row[2], row[0]))
                            else:
                                # not supported yet
                                pass
                    if (guild is None or role is None) and (not network_error and not network_error2):
                        to_delete_roles.append((row[2], row[0]))
        
        if len(to_delete_roles) > 0 :
            remove_global_time_role_querry = """
            DELETE FROM Global_time_role
            WHERE(id=? AND guild_id=?)
            """
            await self.connection.executemany(remove_global_time_role_querry, to_delete_roles)


    async def get_all_expired_recurrent_roles(self) -> AsyncGenerator[tuple[int, int, str, timedelta, datetime]]:
        select = """
        SELECT r.id, r.guild_id, r.next_datetime, g.timezone, r.deltatime
        FROM Recurrent_time_role as r INNER JOIN Guild as g
        ON g.id = r.guild_id;
        """
        async with self.connection.execute(select) as cursor:
            async for row in cursor:
                if row[3] is None:
                    now = datetime.now()
                else:
                    now = datetime.now(tz=pytz.timezone(row[3]))
                if now.strftime(datetime_strptime) > row[2]:
                    yield (row[1], row[0], row[2], timedelta(seconds=row[4]), now)

    async def update_next_datetime_recurrent_roles(self, recurrents_roles: list[tuple[str, int, int]]) -> None:
        remove_querry = """
        UPDATE Recurrent_time_role
        SET next_datetime = ?
        WHERE(id=? AND guild_id=?);
        """
        await self.connection.executemany(remove_querry, recurrents_roles)
            
    async def remove_member_time_role(self, role_id: int, member_id: int, guild_id: int) -> None:
        remove_member_time_role_querry = """
        DELETE FROM Member_time_role
        WHERE(id=? AND member_id=? AND guild_id=?)
        """
        await self.connection.execute(remove_member_time_role_querry, (role_id, member_id, guild_id))
        
    async def remove_guild(self, guild_id: int, commit: bool = False):
        remove_member_time_role_querry = """
        DELETE FROM Guild
        WHERE(id=?)
        """
        query = "PRAGMA foreign_keys = ON;"
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            await cursor.execute(remove_member_time_role_querry, (guild_id,))
            if commit:
                await self.commit()
            
    async def remove_member(self, member_id: int, guild_id: int):
        querry = """
        DELETE FROM Member_time_role
        WHERE(member_id=? AND guild_id=?)
        """
        await self.connection.execute(querry, (member_id, guild_id))

    async def remove_recurrent_time_role(self, role_id: int, guild_id: int):
        querry = """
        DELETE FROM Recurrent_time_role
        WHERE(id=? AND guild_id=?)
        """
        await self.connection.execute(querry, (role_id, guild_id))
        
    async def remove_server_time_role(self, role_id: int, guild_id: int):
        remove_server_time_role_querry = """
        DELETE FROM Time_role
        WHERE(id=? AND guild_id=?)
        """
        remove_member_time_role_querry = """
        DELETE FROM Member_time_role
        WHERE(id=? AND guild_id=?)
        """
        await self.connection.execute(remove_server_time_role_querry, (role_id, guild_id))
        await self.connection.execute(remove_member_time_role_querry, (role_id, guild_id))
        
    async def remove_global_time_role(self, role_id: int, guild_id: int) -> None:
        remove_global_time_role_querry = """
        DELETE FROM Global_time_role
        WHERE(id=? AND guild_id=?)
        """
        await self.connection.execute(remove_global_time_role_querry, (role_id, guild_id))
        
    async def remove_unused_guild(self, bot: TimeRoleBot) -> int:
        guild_ids = set()
        to_delete = []
        
        for guild in bot.guilds:
            guild_ids.add(guild.id)
        select = """
        SELECT id
        FROM
            Guild
        """
        async with self.connection.execute(select) as cursor:
            async for row in cursor:
                if row[0] not in guild_ids:
                    to_delete.append(row)
        remove_member_time_role_querry = """
        DELETE FROM Guild
        WHERE(id=?)
        """
        query = "PRAGMA foreign_keys = ON;"
        async with self.connection.cursor() as cursor:
            await cursor.execute(query)
            await cursor.executemany(remove_member_time_role_querry, to_delete)
        await self.commit()
        return len(to_delete)
    
    async def get_server_count(self):
        query = """
        SELECT COUNT(*)
        FROM Guild;
        """
        result = await self._get_first_in_database(query)
        if result is None:
            return 0
        return result[0]
    
    def calculate_mean(self, result, server_count):
        if len(result) == 0:
            return 0
        total = 0
        for row in result:
            total += sum(row)
        return round(total / len(result), 2), round(total / server_count, 2)
    
    async def get_time_roles_counts(self, guild_id: int):
        query = """
        SELECT COUNT(*)
        FROM Member_time_role 
        WHERE(guild_id=?) ;
        """
        result = await self._get_first_in_database(query, (guild_id,))
        return result[0]
    
    async def get_time_roles_counts_avg(self):
        query = """
        SELECT COUNT(*)
        FROM Member_time_role 
        GROUP BY guild_id;
        """
        result = await self.connection.execute_fetchall(query)
        return self.calculate_mean(result, await self.get_server_count())

    async def get_server_time_roles_counts(self, guild_id: int):
        query = """
        SELECT COUNT(*)
        FROM Time_role 
        WHERE(guild_id=?) ;
        """
        result = await self._get_first_in_database(query, (guild_id,))
        return result[0]
    
    async def get_server_time_roles_counts_avg(self):
        query = """
        SELECT COUNT(*)
        FROM Time_role
        GROUP BY guild_id;
        """
        result = await self.connection.execute_fetchall(query)
        return self.calculate_mean(result, await self.get_server_count())
    
    async def get_global_time_roles_counts(self, guild_id: int):
        query = """
        SELECT COUNT(*)
        FROM Global_time_role 
        WHERE(guild_id=?) ;
        """
        result = await self._get_first_in_database(query, (guild_id,))
        return result[0]
    
    async def get_global_time_roles_counts_avg(self):
        query = """
        SELECT COUNT(*)
        FROM Global_time_role
        GROUP BY guild_id;
        """
        result = await self.connection.execute_fetchall(query)
        return self.calculate_mean(result, await self.get_server_count())
    
    async def backup(self, file: str):
        async with aiosqlite.connect(file) as db_backup:
            await self.commit()
            async with aiosqlite.connect(DATABASE) as current_db:
                await current_db.backup(db_backup)
          
    async def close(self) -> None:
        await self.commit()
        await self.connection.close()
        self.logger.info("The database got closed and commited")
        self.connection = None
        
    async def commit(self) -> None:
        await self.connection.commit()
  

