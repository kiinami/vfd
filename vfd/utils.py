from datetime import datetime

logger_format = "{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {name:<15} | {message}"

def now_to_the_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0, tzinfo=None)
