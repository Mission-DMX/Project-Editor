import time


def format_seconds(seconds: float):
    return time.strftime('%H:%M:%S.{}'.format(int((seconds * 1000) % 1000), time.gmtime(int(seconds))))
