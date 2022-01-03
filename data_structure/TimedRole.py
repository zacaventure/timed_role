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
    
    def __eq__(self, other):
        return self.roleId == other.roleId and self.numberOfDaysToKeep == other.numberOfDaysToKeep and self.addedTime == other.addedTime

    def __lt__(self, other):
        return self.getHowManyDayRemaining() < other.getHowManyDayRemaining()