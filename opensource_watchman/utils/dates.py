import datetime
from typing import Optional


def parse_iso_datetime(iso_datetime: str) -> Optional[datetime.datetime]:
    if iso_datetime.endswith('Z'):
        iso_datetime = iso_datetime[:-1]
    try:
        return datetime.datetime.fromisoformat(iso_datetime)
    except ValueError:
        return None
