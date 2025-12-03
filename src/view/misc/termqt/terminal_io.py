"""Terminal IO Adapter abstract class."""

import os
import time
import struct
import select
import signal
import logging
import threading
from abc import ABC, abstractmethod


class TerminalIO(ABC):
    """TerminalIO abstract class.

    This class provides io functions that communciate with the Terminal
    and the pty (pseudo-tty) of a program.
    """

    @abstractmethod
    def spawn(self):
        """Implement process spawning mechanics here."""
        pass

    @abstractmethod
    def resize(self, rows: int, cols: int):
        """Gets called when terminal is resized.

        Unit: width and height in characters.
        """
        pass

    @abstractmethod
    def write(self, buffer: bytes):
        """Callback will be called when user inputs something into terminal."""
        pass

    @abstractmethod
    def terminate(self):
        """Method must kill connected process."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Getter to check if the process is still alive."""
        return True
