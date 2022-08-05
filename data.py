import datetime
import logging

import discord
from data_structure.Member import Member
from data_structure.Server import Server
import pickle
import os

from data_structure.TimedRole import TimedRole


class Data:
    SAVE_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data.bin")

    def __init__(self) -> None:
        self.loadData()
        self.logger = logging.getLogger("discord_data")
        self.logger.setLevel(logging.INFO)
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "data.log")
        handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)
        self.longestTimedelta = datetime.timedelta(days=-1)
    
    def getServer(self, serverId: int) -> Server:
        server = None
        for serverItr in self.servers:
            if serverItr.serverId == serverId:
                server = serverItr
                break
        if server is None:
            server = Server(serverId)
            self.servers.append(server)
        return server
            
    
    def getMember(self, serverId:int, memberId: int, server=None) -> Member:
        if server is None:
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
    
    def addTimedRole(self, serverId:int, userId: int, roleId : int, saveData=True, server=None, member=None) -> None:
        if server is None:
            server = self.getServer(serverId)
        if member is None:
            member = self.getMember(serverId, userId, server=server)
        
        for timedRole in member.timedRole:
            if timedRole.roleId == roleId:
                return
        if roleId in server.timedRoleOfServer:
            member.timedRole.append(TimedRole(roleId, server.timedRoleOfServer[roleId]))
            if saveData:
                self.saveData()
        
    def loadData(self) -> None:
        if os.path.isfile(Data.SAVE_FILE):
            with open(Data.SAVE_FILE,'rb') as f:
                self.servers = pickle.load(f)
        else:
            self.servers = []
                
    def saveData(self, file = None) -> None:
        start = datetime.datetime.now()
        if file is None:
            with open(Data.SAVE_FILE,'wb') as f:
                pickle.dump(self.servers, f)
        else:
            with open(file,'wb') as f:
                pickle.dump(self.servers, f)
        delta = datetime.datetime.now()-start
        if delta > self.longestTimedelta:
            self.logger.log(logging.INFO, "New longest write: {}".format(delta))
            self.longestTimedelta = delta
            
    def delete_time_role(self, role_id: int, server_id: int,
                         remove_server: bool = True,
                         remove_role_in_members: bool = True,
                         remove_global: bool = True,
                         server: Server = None):
        changes = False
        if server is None:
            server = self.getServer(server_id)
        
        if remove_server:
            if role_id in server.timedRoleOfServer:
                changes = True
                del server.timedRoleOfServer[role_id]
            
        if remove_global:
            isIn = False
            pos = 0
            for globalTimeRole in server.globalTimeRoles:
                if globalTimeRole.roleId == role_id:
                    isIn=True
                    break
                pos += 1
            if isIn:
                changes = True
                del server.globalTimeRoles[pos]
        
        if remove_role_in_members:
            for member in server.members:
                isIn = False
                pos = 0
                for time_role in member.timedRole:
                    if time_role.roleId == role_id:
                        isIn = True
                        break
                    pos += 1
                if isIn:
                    changes = True
                    del member.timedRole[pos]
        if changes:
            self.saveData()
        return changes
    
    def remove_member(self, member_id: int, server_id: int):
        server = self.getServer(server_id)
        pos = 0
        isIn = False
        for member_server in server.members:
            if member_server.memberId == member_id:
                isIn = True
                break
            pos += 1
        if isIn:
            del server.members[pos]
            self.saveData()