from datetime import datetime

# Returns the current UTC in milliseconds
def current_utc_ms():
    return int(1000.0 * datetime.now().timestamp())

# Returns the current GMT+1 time in seconds
def current_time_s():
    return int(datetime.now().timestamp()) + 3600 * 2

# Returns the UTC time of the start of the current day in seconds
def start_current_utc_s():
    start_utc = 3600 * 24 * int(datetime.now().timestamp() / (3600 * 24))
    return start_utc