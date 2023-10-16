from datetime import datetime, timedelta
import time

import pytz


def parse_unixtime(epoch, format="%Y-%m-%d %H:%M:%S", timezone=None) -> str:
    local_time = time.localtime(epoch)

    readable_time = time.strftime(format, local_time)

    utc_dt = datetime.utcfromtimestamp(epoch).replace(tzinfo=pytz.utc)

    if timezone:
        try:
            target_tz = pytz.timezone(timezone)
            localized_dt = utc_dt.astimezone(target_tz)
        except Exception as e:
            raise ValueError(f"Invalid timezone: {e}")
    else:
        localized_dt = utc_dt

    readable_time = localized_dt.strftime(format)

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


def date_add(dt: str, delta: int):
    '''
    dt: yyyy-mm-dd
    delta: days
    '''

    dt = datetime.strptime(dt, "%Y-%m-%d")
    dt = dt + timedelta(days=delta)
    return dt.strftime("%Y-%m-%d")


def date_diff(end: str, start: str):
    '''
    end: yyyy-mm-dd
    start: yyyy-mm-dd
    '''

    end = datetime.strptime(end, "%Y-%m-%d")
    start = datetime.strptime(start, "%Y-%m-%d")
    return (end - start).days
