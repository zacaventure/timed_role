import datetime

class TimedRole:
    def __init__(self, roleId: str, numberOfDaysToKeep: int) -> None:
        self.roleId = roleId
        self.addedTime = datetime.datetime.now()
        self.numberOfDaysToKeep = numberOfDaysToKeep
        
    def isExpire(self) -> bool:
        now = datetime.datetime.now()
        delta = now - self.addedTime
        return delta.days >= self.numberOfDaysToKeep
    
    def getHowManyDayRemaining(self):
        now = datetime.datetime.now()
        delta = now - self.addedTime
        return self.numberOfDaysToKeep - delta.days