import time


def format_seconds(seconds: float):
    millis = int((seconds * 1000) % 1000)
    return time.strftime('%H:%M:%S.{}'.format(millis), time.gmtime(int(seconds)))
