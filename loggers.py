from datetime import datetime
import os
import logging
from constant import LOCAL_TIME_ZONE, LOG_DIR_PATH

def createLoggers() -> None:
    logging.Formatter.converter = lambda *args: datetime.now(tz=LOCAL_TIME_ZONE).timetuple()

    if not os.path.exists(LOG_DIR_PATH):
        os.mkdir(LOG_DIR_PATH)
        
    logger = logging.getLogger("commands")
    logger.setLevel(logging.ERROR)
    file = os.path.join(LOG_DIR_PATH, "commands.log")
    handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s:%(message)s'))
    logger.addHandler(handler)

    loggerStart = logging.getLogger("start")
    loggerStart.setLevel(logging.INFO)
    file = os.path.join(LOG_DIR_PATH, "start.log")
    handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s:%(message)s'))
    loggerStart.addHandler(handler)
    
    logger = logging.getLogger("discord_backups")
    logger.setLevel(logging.INFO)
    file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "backups.log")
    handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s:%(message)s'))
    logger.addHandler(handler)
    
    logger = logging.getLogger("discord_time_checker")
    logger.setLevel(logging.INFO)
    file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "time_checker.log")
    handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    logger.addHandler(handler)
    
    logger = logging.getLogger("bot_events")
    logger.setLevel(logging.INFO)
    file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs", "bot_events.log")
    handler = logging.FileHandler(filename=file, encoding="utf-8", mode="w")
    handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    logger.addHandler(handler)