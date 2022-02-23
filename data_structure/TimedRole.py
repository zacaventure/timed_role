import datetime

class TimedRole:
    def __init__(self, roleId: str, timeToKeep: datetime.timedelta) -> None:
        self.roleId = roleId
        self.addedTime = datetime.datetime.now()
        self.timeToKeep = timeToKeep
        
    def isExpire(self) -> bool:
        now = datetime.datetime.now()
        delta = now - self.addedTime
        return delta >= self.timeToKeep
    
    def getRemainingTimeDelta(self):
        now = datetime.datetime.now()
        delta = now - self.addedTime
        return self.timeToKeep - delta
    
    def __eq__(self, other):
        return self.roleId == other.roleId and self.numberOfDaysToKeep == other.numberOfDaysToKeep and self.addedTime == other.addedTime

    def __lt__(self, other):
        return self.getRemainingTimeDelta() < other.getRemainingTimeDelta()