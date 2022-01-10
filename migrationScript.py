from data import Data
from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.Server import Server
data = Data()

newServers = []
for server in data.servers:
    newGlobal = []
    for globalRole in server.globalTimeRoles:
        globalRoleNew = GlobalTimedRole(globalRole.roleId, globalRole.endDate)
        newGlobal.append(globalRoleNew)
    server.globalTimeRoles = newGlobal
    newServer = Server(server.serverId)
    newServer.members = server.members
    newServer.timedRoleOfServer = server.timedRoleOfServer
    newServer.globalTimeRoles = server.globalTimeRoles
    newServers.append(newServer)
    
data.servers = newServers

print("Migration Script completed !")
data.saveData()