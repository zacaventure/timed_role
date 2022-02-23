import datetime
from secretstorage import Item
from data import Data
from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.Server import Server
from data_structure.TimedRole import TimedRole
data = Data()

newServers = []
for server in data.servers:
    newGlobal = []
    for globalRole in server.globalTimeRoles:
        globalRoleNew = GlobalTimedRole(globalRole.roleId, globalRole.endDate)
        newGlobal.append(globalRoleNew)
    newTimeRoles = {}
    for timeRole, numberOfDays in server.timedRoleOfServer.items():
        newTimeRoles[timeRole] = datetime.timedelta(days=numberOfDays)
    server.globalTimeRoles = newGlobal
    newServer = Server(server.serverId)
    newServer.members = server.members
    newServer.timedRoleOfServer = newTimeRoles
    newServer.globalTimeRoles = server.globalTimeRoles
    newServer.timezone = server.timezone
    for member in server.members:
        newMemberTimeRoles = []
        for timeRole in member.timedRole:
            try:
                newMemberTimeRole = TimedRole(timeRole.roleId, datetime.timedelta(days=timeRole.numberOfDaysToKeep))
                newMemberTimeRole.addedTime = timeRole.addedTime
                newMemberTimeRoles.append(newMemberTimeRole)
            except:
                newMemberTimeRole = TimedRole(timeRole.roleId, datetime.timedelta(days=timeRole.timeToKeep))
                newMemberTimeRole.addedTime = timeRole.addedTime
                newMemberTimeRoles.append(newMemberTimeRole)
        member.timedRole = newMemberTimeRoles
    newServers.append(newServer)
    
data.servers = newServers

print("Migration Script completed !")
data.saveData()