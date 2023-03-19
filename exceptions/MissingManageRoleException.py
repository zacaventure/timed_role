class MissingManageRoleException(Exception):
    def __init__(self) -> None:
        super().__init__("The bot is missing the manage_roles permissions on your server")
