import datetime

class GlobalTimedRole:
    def __init__(self, roleId: str, endDate: datetime.datetime) -> None:
        self.roleId = roleId
        self.endDate = endDate
        
    def isExpire(self) -> bool:
        now = datetime.datetime.now()
        return now >= self.endDate
    
    def getRemainingDays(self) -> int:
        now = datetime.datetime.now()
        return round((self.endDate-now).total_seconds()/86400, 2)
    
    def __eq__(self, other):
        return self.roleId == other.roleId and self.endDate == other.endDate

    def __lt__(self, other):
        return self.endDate < other.endDate