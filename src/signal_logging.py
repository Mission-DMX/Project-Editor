""" logging Handler to broadcast formatted log massages"""
import logging

from model.broadcaster import Broadcaster


class SignalLoging(logging.Handler):
    """logging_view Handler"""

    def __init__(self) -> None:
        super().__init__()
        self._broadcaster = Broadcaster()

    def emit(self, record: logging.LogRecord) -> None:
        """emit logging message"""
        msg: str = self.format(record)
        self._broadcaster.log_message.emit(msg)
