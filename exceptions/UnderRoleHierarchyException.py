from discord import Role


class UnderRoleHierarchyException(Exception):

    __slots__ = ("role",)
    def __init__(self, role: Role) -> None:
        super().__init__(f"The role {role.mention} is higher than the highest role of the bot timed_role. The bot cannot manipulate that role. Please change the role order if you want to create a timed role")
        self.role = role