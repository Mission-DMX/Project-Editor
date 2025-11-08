"""Basic dmx channel with 256 values"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

from model import Broadcaster

if TYPE_CHECKING:
    from model import Universe


class Channel(QtCore.QObject):
    """Basic dmx channel with 256 values"""

    updated: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, channel_address: int, universe: Universe) -> None:
        """Constructs a channel."""
        super().__init__(None)
        if not (0 <= channel_address <= 511):
            raise ValueError(f"Tried to create a channel with address {channel_address}")
        self._address: int = channel_address
        self._value: int = 0
        self._broadcaster = Broadcaster()
        self._universe = universe

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

    @property
    def value(self) -> int:
        """The current value of the channel"""
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        """Updates the value of the channel.
        Must be between 0 and 255.

        Raises:
            ValueError: The value is below 0 or above 255.
        """
        if not (0 <= value <= 511):
            raise ValueError(f"Tried to set channel {self._address} to {value}.")
        self._value = value
        self.updated.emit(value)
        self._broadcaster.send_universe_value.emit(self._universe)
