from datetime import datetime, UTC


def now_to_the_hour() -> datetime:
    return datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
