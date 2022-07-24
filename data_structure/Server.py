class Server:
    def __init__(self, serverId : int) -> None:
        self.serverId = serverId
        self.members = []
        self.timedRoleOfServer = {}
        self.globalTimeRoles = []
        self.timezone = None