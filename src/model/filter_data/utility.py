"""Filter model utility methods."""

import time


def format_seconds(seconds: float) -> str:
    """Format a given number of seconds into a time.

    Args:
        seconds: Number of seconds to format.

    Returns: Formatted time as hours, minutes and seconds.

    """
    millis = int((seconds * 1000) % 1000)
    return f"{time.strftime('%H:%M:%S', time.gmtime(int(seconds)))}.{millis:0>3}"
