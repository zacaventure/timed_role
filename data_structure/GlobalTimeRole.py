import datetime

class GlobalTimedRole:
    def __init__(self, roleId: str, endDate: datetime.datetime) -> None:
        self.roleId = roleId
        self.endDate = endDate
        
    def isExpire(self, timezone) -> bool:
        now = datetime.datetime.now(tz=timezone)
        self.endDate = self.convertTo(self.endDate, timezone)
        return now >= self.endDate
    
    def getRemainingTimeDelta(self, timezone) -> datetime.timedelta:
        now = datetime.datetime.now(tz=timezone)
        self.endDate = self.convertTo(self.endDate, timezone)
        return self.endDate-now
    
    def convertTo(self, datetime: datetime.datetime, targetTimeZone: datetime.timezone) -> datetime.datetime:
        if targetTimeZone is None or datetime.tzinfo == targetTimeZone:
            return datetime
        return datetime.astimezone(targetTimeZone)
    
    def printEndDate(self)->str:
        if self.endDate.tzinfo is not None:
            return "{} in {}".format(self.endDate.strftime("%Y-%m-%d at %H:%M:%S"), self.endDate.tzinfo)
        else:
            return self.endDate.strftime("%Y-%m-%d at %H:%M:%S")
    
    def __eq__(self, other):
        return self.roleId == other.roleId and self.endDate == other.endDate

    def __lt__(self, other):
        return self.endDate < other.endDate