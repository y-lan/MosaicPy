import time
from datetime import datetime, timedelta

import pytz


def from_unixtime(epoch, format="%Y-%m-%d %H:%M:%S", timezone=None) -> str:
    """
    Convert a Unix epoch time to a formatted string representation.

    The function takes a Unix epoch time and converts it to a human-readable string format. 
    Optionally, it can also convert the time to a specified timezone.

    Parameters:
    epoch (int): The Unix epoch time (number of seconds since January 1, 1970, 00:00:00 UTC).
    format (str, optional): The format string to control the output format of the date and time.
        The default format is "%Y-%m-%d %H:%M:%S", which corresponds to "Year-Month-Day Hour:Minute:Second".
    timezone (str, optional): A string representing the target timezone (e.g., "America/New_York"). 
        If not specified, UTC is used.

    Returns:
    str: The formatted date and time string in the specified format and timezone.

    Raises:
    ValueError: If the specified timezone is invalid.

    Example usage:
    >>> from_unixtime(1609459200)
    '2021-01-01 00:00:00'

    >>> from_unixtime(1609459200, timezone="America/New_York")
    '2020-12-31 19:00:00'
    """
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


def from_unixtime_jp(epoch, format="%Y-%m-%d %H:%M:%S") -> str:
    return from_unixtime(epoch, format, "Asia/Tokyo")


def to_unixtime(dt: str, format: str = None, timezone: str = 'UTC') -> int:
    """
    Converts a datetime string to a Unix timestamp (number of seconds since Jan 1, 1970, UTC).

    The function supports multiple datetime string formats. If the format is not provided, it infers the format
    based on the length of the datetime string. Supported formats include:
    - YYYY-MM-DD (10 characters)
    - YYYY-MM-DD HH:MM:SS (19 characters)
    - YYYY-MM-DD HH:MM:SS.sss (23 characters)
    - ISO 8601 format (24 characters, e.g., YYYY-MM-DDTHH:MM:SS+0000)

    Args:
    - dt (str): The datetime string to be converted.
    - format (str, optional): The format of the datetime string. If None, the format is inferred. Defaults to None.
    - timezone (str, optional): The timezone of the datetime string. If None, timezone is considered as included in the datetime string (for ISO 8601 format). Defaults to 'UTC'.

    Returns:
    - int: The Unix timestamp corresponding to the provided datetime string.

    Raises:
    - ValueError: If the datetime string format is unknown or cannot be inferred.

    Example:
    >>> to_unixtime("2023-11-28")
    1669593600
    >>> to_unixtime("2023-11-28T12:30:00+0000")
    1669630200
    """
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


def to_unixtime_jp(dt: str, format: str = None) -> int:
    return to_unixtime(dt, format, "Asia/Tokyo")


def get_dt(tz='UTC', format="%Y-%m-%d"):
    return datetime.now(pytz.timezone(tz)).strftime(format)


def get_dt_local(format="%Y-%m-%d"):
    return datetime.now().strftime(format)


def get_dt_jp(format="%Y-%m-%d"):
    return get_dt('Asia/Tokyo', format)


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
