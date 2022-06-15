import datetime

class GlobalTimedRole:
    def __init__(self, roleId: str, endDate: datetime.datetime) -> None:
        self.roleId = roleId
        self.endDate = endDate
        
    def isExpire(self, timezone) -> bool:
        now = datetime.datetime.now(tz=timezone)
        self.endDate = self.convertTo(self.endDate, timezone)
        return now.strftime("%Y-%m-%d %H:%M:%S") >= self.endDate.strftime("%Y-%m-%d %H:%M:%S")
    
    def getRemainingTimeDelta(self, timezone) -> datetime.timedelta:
        now = datetime.datetime.now(tz=timezone)
        self.endDate = self.convertTo(self.endDate, timezone)
        return self.endDate-now
    
    def convertTo(self, targetDatetime: datetime.datetime, targetTimeZone: datetime.timezone) -> datetime.datetime:
        if targetTimeZone is None or datetime.tzinfo == targetTimeZone:
            return targetDatetime
        return datetime.datetime(year=targetDatetime.year, month=targetDatetime.month,
                                 day=targetDatetime.day, hour=targetDatetime.hour,
                                 minute=targetDatetime.minute, second=targetDatetime.second,
                                 microsecond=targetDatetime.microsecond, 
                                 tzinfo=targetTimeZone)

    
    def printEndDate(self)->str:
        if self.endDate.tzinfo is not None:
            return "{} in {}".format(self.endDate.strftime("%Y-%m-%d at %H:%M:%S"), self.endDate.tzinfo)
        else:
            return self.endDate.strftime("%Y-%m-%d at %H:%M:%S")
    
    def __eq__(self, other):
        return self.roleId == other.roleId and self.endDate == other.endDate

    def __lt__(self, other):
        return self.endDate < other.endDate