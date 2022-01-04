from data import Data
from data_structure.GlobalTimeRole import GlobalTimedRole
from data_structure.Server import Server
data = Data()

for server in data.servers:
    newGlobal = []
    for globalRole in server.globalTimeRoles:
        globalRoleNew = GlobalTimedRole(globalRole.roleId, globalRole.endDate)
        newGlobal.append(globalRoleNew)
    server.globalTimeRoles = newGlobal

print("Migration Script for the new method for globalTimedRole completed !")
data.saveData()