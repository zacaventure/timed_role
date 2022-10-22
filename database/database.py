
from datetime import datetime, timedelta
from cogs.Util import get_or_fetch_guild, get_or_fetch_member, get_or_fetch_role
from constant import datetime_strptime
import aiosqlite
import os
import pytz
from discord.ext.commands import Bot
import aiohttp
import sqlite3

from constant import DATABASE

update_member_time_role_querry = """
UPDATE Member_time_role
SET deltatime = {}
WHERE id = {} AND member_id = {} AND guild_id = {} ;"""

async def create_database():
    database_str = None
    database_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "create_database.sql")
    with open(database_path, "r") as file:
        database_str = file.read()
     
    async with aiosqlite.connect(DATABASE) as db:
        await db.executescript(database_str)
        await db.commit()

async def drop_database():
    drop = """
    DROP TABLE IF EXISTS Guild;
    DROP TABLE IF EXISTS Member;
    DROP TABLE IF EXISTS Member_time_role;
    DROP TABLE IF EXISTS Time_role;
    DROP TABLE IF EXISTS Global_time_role;"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.executescript(drop)
        await db.commit()
    
async def insert_if_not_exist_guild(id: int, timezone = None):
    insert_guild_querry = """
    INSERT OR IGNORE INTO Guild (id, timezone)
    VALUES(?, ?);
    """
    await _execute_in_database(insert_guild_querry, (id, timezone))

    
async def get_timezone(guild_id: int):
    select = """
    SELECT timezone
    FROM
        Guild
    WHERE ( id = ?) ;
    """
    timezone = await _get_first_in_database(select, (guild_id,))
    if timezone is None:
        return timezone
    return timezone[0]
    
async def insert_member_time_role(role_id: int, deltatime: timedelta, 
                                  member_id: int, guild_id: int, creation_time: datetime=None) -> None:
    
    insert_member_time_role_querry = """
    INSERT OR IGNORE INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
    VALUES (?, ?, ?, ?, ?) ;"""
    
    if creation_time is None:
        creation_time = datetime.now()
    
    await _execute_in_database(insert_member_time_role_querry, 
                               (role_id, creation_time.strftime(datetime_strptime), 
                                deltatime.total_seconds(), member_id, guild_id)
                               )
    
def insert_member_time_role_sync(role_id: int, deltatime: timedelta, 
                                  member_id: int, guild_id: int) -> None:
    
    insert_member_time_role_querry = """
    INSERT OR IGNORE INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
    VALUES (?, ?, ?, ?, ?) ;"""
    
    with sqlite3.connect(DATABASE) as db:
        db.execute(insert_member_time_role_querry, (role_id, datetime.now().strftime(datetime_strptime), 
                                deltatime.total_seconds(), member_id, guild_id))
        db.commit()
    
async def insert_all_member_time_role(member_time_role_list) -> None:
    
    insert_member_time_role_querry = """
    INSERT OR IGNORE INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
    VALUES (?, ?, ?, ?, ?) ;"""
    
    async with aiosqlite.connect(DATABASE) as db:
        await db.executemany(insert_member_time_role_querry, member_time_role_list)
        await db.commit()
    
async def insert_or_update_member_time_role(role_id: int, deltatime: timedelta, 
                                  member_id: int, guild_id: int) -> float:
    
    insert_member_time_role_querry = """
    INSERT OR IGNORE INTO Member_time_role (id, creation_time, deltatime, member_id, guild_id)
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
    
    member_time_role = await _get_first_in_database(select, select_data)
    if member_time_role is None:
        await _execute_in_database(insert_member_time_role_querry, insert_data)
        return None
    else:
        update_data = (deltatime.total_seconds(), 
                       datetime.now().strftime(datetime_strptime), role_id, member_id, guild_id)
        await _execute_in_database(update_member_time_role_querry, update_data)
        return member_time_role[0]
        
async def insert_time_role(role_id: int, deltatime: timedelta, guild_id: int):
    await insert_if_not_exist_guild(guild_id, None)
    insert_time_role_querry = """
    INSERT INTO Time_role (id, guild_id, deltatime)
    VALUES({}, {}, {});
    """
    
    update_time_role_querry = """
    UPDATE Time_role
    SET deltatime = {}
    WHERE id = {} AND guild_id = {} ;"""
    
    previous_deltime = await get_time_role_deltatime(role_id, guild_id)
    if previous_deltime is not None:
        await _execute_in_database(update_time_role_querry.format(deltatime.total_seconds(), role_id, guild_id))
    else:
        await _execute_in_database(insert_time_role_querry.format(role_id, guild_id, deltatime.total_seconds()))
    return previous_deltime

async def insert_global_time_role(role_id: int, end_datetime: datetime, guild_id: int, delete_from_guild: bool):
    await insert_if_not_exist_guild(guild_id, None)
    insert_time_role_querry = """
    INSERT INTO Global_time_role (id, end_datetime, guild_id, delete_from_guild)
    VALUES(?, ?, ?, ?);
    """
    
    update_time_role_querry = """
    UPDATE Global_time_role
    SET end_datetime = ?
    WHERE id = ? AND guild_id = ? ;"""
    
    previous_datetime = await get_global_time_role(role_id, guild_id)
    if previous_datetime is not None:
        previous_datetime = previous_datetime[1]
        await _execute_in_database(update_time_role_querry, (end_datetime.strftime(datetime_strptime), role_id, guild_id))
    else:
        await _execute_in_database(insert_time_role_querry, (role_id, end_datetime.strftime(datetime_strptime), guild_id, delete_from_guild))
    return previous_datetime

async def insert_timezone(timezone: str, guild_id: int):
    await insert_if_not_exist_guild(guild_id)
    old_timezone = await get_timezone(guild_id)
    
    update_timezone_querry = """
    UPDATE Guild
    SET timezone = ?
    WHERE id = ? ;"""
    
    update_timezone_global_time_roles_querry = """
    UPDATE Global_time_role
    SET end_datetime = ?
    WHERE id = ? AND guild_id = ?;"""
    
    await _execute_in_database(update_timezone_querry, (timezone, guild_id))
    global_time_roles = await get_all_global_time_roles(guild_id)
    updates = []
    for id, end_datetime in global_time_roles:
        end_datetime = datetime.strptime(end_datetime, datetime_strptime)
        new_end_datetime = datetime(year=end_datetime.year, month=end_datetime.month,
                                 day=end_datetime.day, hour=end_datetime.hour,
                                 minute=end_datetime.minute, second=end_datetime.second,
                                 microsecond=end_datetime.microsecond, 
                                 tzinfo=pytz.timezone(timezone))
        updates.append((new_end_datetime.strftime(datetime_strptime), id, guild_id))
    async with aiosqlite.connect(DATABASE) as db:
        await db.executemany(update_timezone_global_time_roles_querry, updates)
        await db.commit()
    return old_timezone
    

async def _is_in_database(querry: str, data=None) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(querry, data)
        result = await cursor.fetchone()
        if result[0] == 0:
            return False
        return True
    
async def _execute_in_database(querry: str, data=None) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(querry, data)
        await db.commit()
        
async def _get_first_in_database(querry: str, data=None) ->  aiosqlite.Row:
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(querry, data) as cursor:
            cursor: aiosqlite.Cursor
            result = await cursor.fetchone()
            if result is None:
                return None
            else:
                return result
            
        
async def get_time_role_deltatime(role_id: int, guild_id: int):
    select = """
    SELECT deltatime
    FROM
        Time_role
    WHERE ( id = {} AND guild_id = {}) ;
     """.format(role_id, guild_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(select) as cursor:
            cursor: aiosqlite.Cursor
            result = await cursor.fetchone()
            if result is None:
                return None
            else:
                return result[0]
            
def get_time_role_deltatime_sync(role_id: int, guild_id: int):
    select = """
    SELECT deltatime
    FROM
        Time_role
    WHERE ( id = {} AND guild_id = {}) ;
     """.format(role_id, guild_id)
    with sqlite3.connect(DATABASE) as db:
        result = db.execute(select).fetchone()
        if result is None:
            return None
        else:
            return result[0]

async def get_global_time_role(role_id: int, guild_id: int):
    select = """
    SELECT *
    FROM
        Global_time_role
    WHERE ( id = ? AND guild_id = ?) ;
     """
    return await _get_first_in_database(select, (role_id, guild_id))
async def get_all_server_time_roles(guild_id: int):
    select = """
    SELECT id, deltatime
    FROM 
        Time_role
    WHERE guild_id = ? ;
    """
    async with aiosqlite.connect(DATABASE) as db:
        return await db.execute_fetchall(select, (guild_id,))
    
async def get_all_global_time_roles(guild_id: int):
    select = """
    SELECT id, end_datetime
    FROM
        Global_time_role
    WHERE ( guild_id = ?) ;
    """
    async with aiosqlite.connect(DATABASE) as db:
        return await db.execute_fetchall(select, (guild_id,))
            
async def get_member_time_role(member_id: int, guild_id: int):
    select = """
    SELECT 	id, creation_time, deltatime
    FROM Member_time_role
    WHERE ( member_id = {} AND guild_id = {}) ;
    """.format(member_id, guild_id)
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(select) as cursor:
            cursor: aiosqlite.Cursor
            results = await cursor.fetchall()
            return results
        
async def get_member_time_role_from_guild(role_id: int, guild_id: int):
    select = """
    SELECT 	creation_time, deltatime, member_id
    FROM Member_time_role
    WHERE ( id = ? AND guild_id = ?) ;
    """
    async with aiosqlite.connect(DATABASE) as db:
        return await db.execute_fetchall(select, (role_id, guild_id))


async def is_guild_in_database(guild_id: int):
    exist_guild_querry = """
    SELECT EXISTS(SELECT 1 FROM Guild WHERE id={} LIMIT 1);
    """
    return await _is_in_database(exist_guild_querry.format(guild_id))

async def is_global_time_role_in_database(role_id: int, guild_id: int):
    exist_time_role_querry = """
    SELECT EXISTS(SELECT 1 FROM Global_time_role WHERE(id=? AND guild_id=?) LIMIT 1);
    """
    return await _is_in_database(exist_time_role_querry, (role_id, guild_id))

async def is_member_time_role_in_database(role_id: int, member_id: int, guild_id: int):
    exist_member_time_role_querry = """
    SELECT EXISTS(SELECT 1 FROM Member_time_role WHERE(id={} AND member_id={} AND guild_id={}) LIMIT 1);
    """
    return await _is_in_database(exist_member_time_role_querry.format(role_id, member_id, guild_id))

async def is_time_role_in_database(role_id: int, guild_id: int):
    exist_time_role_querry = """
    SELECT EXISTS(SELECT 1 FROM Time_role WHERE(id={} AND guild_id={}) LIMIT 1);
    """
    return await _is_in_database(exist_time_role_querry.format(role_id, guild_id))

async def remove_expired_time_role(bot: Bot, logger=None):
    to_delete_roles = []
    select = """
    SELECT 	*
    FROM Member_time_role ;
    """
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(select) as cursor:
            async for row in cursor:
                now = datetime.now()
                deltatime = timedelta(seconds=row[2])
                creation_datetime = datetime.strptime(row[1], datetime_strptime)
                if now - creation_datetime > deltatime:
                    guild, network_error = await get_or_fetch_guild(bot, row[4])
                    if guild is not None:
                        member, network_error2 = await get_or_fetch_member(guild, row[3])
                        role, network_error3 = await get_or_fetch_role(guild, row[0])
                        if member is not None and role is not None:
                            try:
                                if role in member.roles:
                                    # the time role will be deleted in the database with on_member_update event
                                    await member.remove_roles(role, reason = "Your role has expired after {}".format(deltatime))
                                else:
                                    to_delete_roles.append((row[0], row[3], row[4]))
                            except aiohttp.client_exceptions.ClientConnectorError:  # type: ignore
                                pass
                            except Exception as e:
                                if logger is not None:
                                    logger.exception("\n On member {}  with roles {}.\n To delete role {} with id {}.\n In server {}, with roles {}\n"
                                    .format(member, member.roles, role, role.id, guild, guild.roles))
                                to_delete_roles.append((row[0], row[3], row[4]))
                    if (guild is None or member is None or role is None) and (not network_error and not network_error2 and not network_error3):
                            to_delete_roles.append((row[0], row[3], row[4]))
    if len(to_delete_roles) > 0 :                     
        remove_member_time_role_querry = """
        DELETE FROM Member_time_role
        WHERE(id=? AND member_id=? AND guild_id=?)
        """
        async with aiosqlite.connect(DATABASE) as db:
            await db.executemany(remove_member_time_role_querry, to_delete_roles)
            await db.commit()
        
async def remove_expired_global_time_role(bot: Bot, logger=None):
    select = """
    SELECT g.id, g.timezone, t.id, t.end_datetime, t.delete_from_guild
    FROM Guild as g INNER JOIN Global_time_role as t
    ON g.id = t.guild_id ;
    """
    to_delete_roles = []
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(select) as cursor:
            async for row in cursor:
                if row[1] is None:
                    now = datetime.now()
                else:
                    now = datetime.now(tz=pytz.timezone(row[1]))
                if now.strftime(datetime_strptime) > row[3]:
                    guild, network_error = await get_or_fetch_guild(bot, row[0])
                    if guild is not None:
                        role, network_error2 = await get_or_fetch_role(guild, row[2])
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
        async with aiosqlite.connect(DATABASE) as db:
            await db.executemany(remove_global_time_role_querry, to_delete_roles)
            await db.commit()
                            
async def remove_member_time_role(role_id: int, member_id: int, guild_id: int):
    remove_member_time_role_querry = """
    DELETE FROM Member_time_role
    WHERE(id=? AND member_id=? AND guild_id=?)
    """
    await _execute_in_database(remove_member_time_role_querry, (role_id, member_id, guild_id))
    
async def remove_guild(guild_id: int):
    remove_member_time_role_querry = """
    DELETE FROM Guild
    WHERE(id=?)
    """
    async with aiosqlite.connect(DATABASE) as db:
        query = "PRAGMA foreign_keys = ON;"
        async with db.cursor() as cursor:
            await cursor.execute(query)
            await cursor.execute(remove_member_time_role_querry, (guild_id,))
            await db.commit()    
    
async def remove_member(member_id: int, guild_id):
    querry = """
    DELETE FROM Member_time_role
    WHERE(member_id=? AND guild_id=?)
    """
    await _execute_in_database(querry, (member_id, guild_id))

async def remove_server_time_role(role_id: int, guild_id: int):
    remove_server_time_role_querry = """
    DELETE FROM Time_role
    WHERE(id=? AND guild_id=?)
    """
    remove_member_time_role_querry = """
    DELETE FROM Member_time_role
    WHERE(id=? AND guild_id=?)
    """
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(remove_server_time_role_querry, (role_id, guild_id))
        await db.execute(remove_member_time_role_querry, (role_id, guild_id))
        await db.commit()
        
async def remove_global_time_role(role_id: int, guild_id: int):
    remove_global_time_role_querry = """
    DELETE FROM Global_time_role
    WHERE(id=? AND guild_id=?)
    """
    await _execute_in_database(remove_global_time_role_querry, (role_id, guild_id))
    
async def remove_unused_guild(bot: Bot):
    guild_ids = set()
    to_delete = []
    
    for guild in bot.guilds:
        guild_ids.add(guild.id)
    select = """
    SELECT id
    FROM
        Guild
    """
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(select) as cursor:
            async for row in cursor:
                if row[0] not in guild_ids:
                    to_delete.append(row)
    remove_member_time_role_querry = """
    DELETE FROM Guild
    WHERE(id=?)
    """
    async with aiosqlite.connect(DATABASE) as db:
        query = "PRAGMA foreign_keys = ON;"
        async with db.cursor() as cursor:
            await cursor.execute(query)
            await cursor.executemany(remove_member_time_role_querry, to_delete)
            await db.commit()
    return len(to_delete)

async def backup(file: str):
    async with aiosqlite.connect(DATABASE) as db:
        async with aiosqlite.connect(file) as db_backup:
            await db.backup(db_backup)
  

