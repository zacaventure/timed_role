import datetime

class GlobalTimedRole:
    def __init__(self, roleId: str, endDate: datetime.datetime) -> None:
        self.roleId = roleId
        self.endDate = endDate
        
    def isExpire(self) -> bool:
        now = datetime.datetime.now()
        return now >= self.endDate