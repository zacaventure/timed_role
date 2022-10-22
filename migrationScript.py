import asyncio
import database.database as database
from data import Data
from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.Server import Server
from data_structure.Member import Member
from data_structure.TimedRole import TimedRole


data = Data()

async def migration():
    await database.create_database()
    i = 1
    for guild in data.servers:
        guild: Server
        timezone = None
        if guild.timezone is not None:
            timezone = str(guild.timezone)
        await database.insert_if_not_exist_guild(guild.serverId, timezone)
        for server_time_role_id, server_time_role_timedelta in guild.timedRoleOfServer.items():
            await database.insert_time_role(server_time_role_id, server_time_role_timedelta, guild.serverId)
        for global_time_role in guild.globalTimeRoles:
            global_time_role: GlobalTimedRole
            await database.insert_global_time_role(global_time_role.roleId, global_time_role.endDate, guild.serverId, True)
        for member in guild.members:
            member: Member
            for role in member.timedRole:
                role: TimedRole
                await database.insert_member_time_role(role.roleId, role.timeToKeep, member.memberId,
                                                       guild.serverId, creation_time=role.addedTime)
        print("{}/{} completed".format(i, len(data.servers)))
        i += 1
  
asyncio.run(migration())
print("migration script complete")