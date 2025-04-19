import time


def format_seconds(seconds: float):
    millis = int((seconds * 1000) % 1000)
    return f"{time.strftime('%H:%M:%S', time.gmtime(int(seconds)))}.{millis:0>3}"
