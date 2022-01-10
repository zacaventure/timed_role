import datetime
from types import DynamicClassAttribute

class GlobalTimedRole:
    def __init__(self, roleId: str, endDate: datetime.datetime) -> None:
        self.roleId = roleId
        self.endDate = endDate
        
    def isExpire(self, timezone) -> bool:
        now = datetime.datetime.now(tz=timezone)
        self.endDate = self.convertTo(self.endDate, timezone)
        return now >= self.endDate
    
    def getRemainingDays(self, timezone) -> int:
        now = datetime.datetime.now(tz=timezone)
        self.endDate = self.convertTo(self.endDate, timezone)
        return round((self.endDate-now).total_seconds()/86400, 2)
    
    def convertTo(self, datetime: datetime.datetime, targetTimeZone: datetime.timezone) -> datetime.datetime:
        if datetime.tzinfo == targetTimeZone:
            return datetime
        if datetime.tzinfo is None:
            return targetTimeZone.localize(datetime)
        return datetime.astimezone(targetTimeZone)
    
    def printEndDate(self)->str:
        return self.endDate.strftime("%Y-%m-%d at %H:%M:%S")
    
    def __eq__(self, other):
        return self.roleId == other.roleId and self.endDate == other.endDate

    def __lt__(self, other):
        return self.endDate < other.endDate