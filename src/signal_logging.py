""" logging Handler to broadcast formatted log massages"""
from logging import Handler, LogRecord

from model.broadcaster import Broadcaster


class SignalLoging(Handler):
    """logging_view Handler"""

    def __init__(self) -> None:
        super().__init__()
        self._broadcaster = Broadcaster()

    def emit(self, record: LogRecord) -> None:
        """emit logging message"""
        msg: str = self.format(record)
        self._broadcaster.log_message.emit(msg)
