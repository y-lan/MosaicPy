from datetime import datetime
import time


def parse_unix(epoch, format="%Y-%m-%d %H:%M:%S") -> str:
    local_time = time.localtime(epoch)
    readable_time = time.strftime(format, local_time)
    return readable_time
