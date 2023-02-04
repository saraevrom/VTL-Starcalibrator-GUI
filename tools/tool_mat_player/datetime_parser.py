import re
from datetime import datetime, timezone
import time




# Y - year, M - month, D - day
# h - hour, m - minute, s - second, ms - millisecond
DATETIME_REGEXES = [
    (r"[\sa-zA-Z]+", None),
    (r"(\d+)-(\d+)-(\d+)", "Y M D"),
    (r"(\d+)\.(\d+)\.(\d+)", "D M Y"),
    (r"(\d+):(\d+):(\d+):(\d+)", "h m s ms"),
    (r"(\d+):(\d+):(\d)+\.(\d+)", "h m s ms"),
    (r"(\d+):(\d+):(\d+)", "h m s"),
    (r"(\d+):(\d+)", "h m")
]

for i in range(len(DATETIME_REGEXES)):
    src, mask = DATETIME_REGEXES[i]
    if mask is not None:
        mask = mask.split()
    DATETIME_REGEXES[i] = (re.compile(src), mask)



def match_string(s, start):
    for regex, mask in DATETIME_REGEXES:
        mat = regex.match(s, pos=start)
        if mat:
            if mask is None:
                return None, mat.end()
            groups = mat.groups()
            assert len(groups) == len(mask)
            return {mask[i]: int(groups[i]) for i in range(len(groups))}, mat.end()
    return None, None

def parse_datetimes(datetime_string, current_dt: datetime):
    start = 0
    data = {
        "Y":current_dt.year, "M":current_dt.month, "D":current_dt.day,
        "h":current_dt.hour, "m":current_dt.minute, "s":current_dt.second, "ms":current_dt.microsecond//1000
    }
    while start < len(datetime_string):
        parsed, end = match_string(datetime_string, start)
        if end is None:
            return None
        start = end
        if parsed is not None:
            data.update(parsed)
    try:
        print(data)
        dt = datetime(year=data["Y"], month=data["M"], day=data["D"],
                      hour=data["h"], minute=data["m"],second=data["s"], microsecond=data["ms"]*1000)
        return (dt - datetime(1970, 1, 1)).total_seconds()
    except ValueError:
        return None