import time


def format_seconds(seconds: float):
    return time.strftime('%H:%M:%S.{0:0>3}'.format((seconds * 1000) % 1000), time.gmtime(int(seconds)))
