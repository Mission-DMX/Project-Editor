"""Filter model utility methods.

format_seconds -- Method to get duration in seconds as human readable string.
"""

import time


def format_seconds(seconds: float) -> str:
    """Format a given number of seconds into a time.

    :param seconds: Number of seconds to format.
    :type seconds: float
    :returns: Formatted time as hours, minutes and seconds.
    """
    millis = int((seconds * 1000) % 1000)
    return f"{time.strftime('%H:%M:%S', time.gmtime(int(seconds)))}.{millis:0>3}"
