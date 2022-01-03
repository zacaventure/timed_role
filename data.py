from data_structure.Member import Member
from data_structure.Server import Server
import pickle
import os

from data_structure.TimedRole import TimedRole


class Data:
    SAVE_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data.bin")

    def __init__(self) -> None:
        self.loadData()
    
    def getServer(self, serverId: str) -> Server:
        server = None
        for serverItr in self.servers:
            if serverItr.serverId == serverId:
                server = serverItr
                break
        if server is None:
            server = Server(serverId)
            self.servers.append(server)
        return server
            
    
    def getMember(self, serverId:str, memberId: str) -> Member:
        server = self.getServer(serverId)
        member = None
        for memberItr in server.members:
            if memberItr.memberId == memberId:
                member = memberItr
                break
        if member is None:
            member = Member(memberId)
            server.members.append(member)

        return member
    
    def addTimedRole(self, serverId:str, userId: str, roleId : str) -> None:
        member = self.getMember(serverId, userId)
        server = self.getServer(serverId)
        
        for timedRole in member.timedRole:
            if timedRole.roleId == roleId:
                return
        if roleId in server.timedRoleOfServer:
            member.timedRole.append(TimedRole(roleId, server.timedRoleOfServer[roleId]))
            self.saveData()
        
    def loadData(self) -> None:
        if os.path.isfile(Data.SAVE_FILE):
            with open(Data.SAVE_FILE,'rb') as f:
                self.servers = pickle.load(f)
        else:
            self.servers = []
                
    def saveData(self) -> None:
        with open(Data.SAVE_FILE,'wb') as f:
            pickle.dump(self.servers, f)