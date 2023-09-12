from datetime import datetime
import time

import pytz


def parse_unixtime(epoch, format="%Y-%m-%d %H:%M:%S") -> str:
    local_time = time.localtime(epoch)
    readable_time = time.strftime(format, local_time)
    return readable_time


def to_unixtime(dt: str, format: str = None, timezone: str = 'UTC') -> int:
    if format is None:
        match len(dt):
            case 10:
                format = "%Y-%m-%d"
            case 19:
                format = "%Y-%m-%d %H:%M:%S"
            case 23:
                format = "%Y-%m-%d %H:%M:%S.%f"
            case 24:
                format = '%Y-%m-%dT%H:%M:%S%z'
                timezone = None
            case _:
                raise ValueError("Unknown datetime format")

    dt = datetime.strptime(dt, format)
    if timezone is not None:
        dt = pytz.timezone(timezone).localize(dt)
    epoch = int(dt.timestamp())
    return epoch
