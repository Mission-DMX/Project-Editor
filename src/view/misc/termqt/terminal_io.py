"""Terminal IO Adapter abstract class."""

import logging
import os
import select
import signal
import struct
import threading
import time
from abc import ABC, abstractmethod


class TerminalIO(ABC):
    """TerminalIO abstract class.

    This class provides io functions that communciate with the Terminal
    and the pty (pseudo-tty) of a program.
    """

    @abstractmethod
    def spawn(self) -> None:
        """Implement process spawning mechanics here."""

    @abstractmethod
    def resize(self, rows: int, cols: int) -> None:
        """Gets called when terminal is resized.

        Unit: width and height in characters.
        """

    @abstractmethod
    def write(self, buffer: bytes) -> None:
        """Callback will be called when user inputs something into terminal."""

    @abstractmethod
    def terminate(self) -> None:
        """Method must kill connected process."""

    @abstractmethod
    def is_alive(self) -> bool:
        """Getter to check if the process is still alive."""
        return True
