class RetryInfo:
    def __init__(self, guild, memberId, roleId) -> None:
        self.guild = guild
        self.memberId = memberId
        self.roleId = roleId
        
    def __hash__(self):
        return hash((self.guild, self.memberId, self.roleId))

    def __eq__(self, other):
        return (self.guild, self.memberId, self.roleId) == (other.guild, other.memberId, other.roleId)

    def __ne__(self, other):
        # Not strictly necessary, but to avoid having both x==y and x!=y
        # True at the same time
        return not(self == other)