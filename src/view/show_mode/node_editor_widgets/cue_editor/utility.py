import time


def format_seconds(seconds: float):
    millis = int((seconds * 1000) % 1000)
    return time.strftime('%H:%M:%S.{0:0>3}'.format(millis), time.gmtime(int(seconds)))
