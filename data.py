class Data:
    """
    servers = {
        serverId1 : {
            userId1: {
                rolesToCheck: [] list<RoleTimeOutChecker>
            }
            userID2:{
                rolesToCheck: [] list<RoleTimeOutChecker>
            }
            ,
            timedRoles: [] list<roleId: str>
        }
    }
    """
        
    ###
    servers = {}
    
    def getServer(self, serverId: str):
        pass
    
    def getUser(self, serverId:str, userId: str):
        server = self.getServer(serverId)
        
    def updateData(self):
        pass