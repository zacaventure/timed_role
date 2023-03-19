class BotNotReadyException(Exception):
    def __init__(self) -> None:
        super().__init__("The bot is not ready, it is booting up")
