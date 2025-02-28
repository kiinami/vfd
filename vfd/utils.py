from datetime import datetime


def now_to_the_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0)
