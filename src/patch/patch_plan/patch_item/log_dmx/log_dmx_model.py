"""Model for logging DMX values for one Universe."""

from __future__ import annotations

from PySide6 import QtCore

from model.universe import NUMBER_OF_CHANNELS


class LogDmxModel(QtCore.QObject):
    """Model for logging DMX values for one Universe."""

    new_value = QtCore.Signal()

    def __init__(self) -> None:
        """DMX values for one Universe."""
        super().__init__()
        self._last_values: list[int] = [0] * NUMBER_OF_CHANNELS
        self._current_values: list[int] = [0] * NUMBER_OF_CHANNELS

    @property
    def current_values(self) -> list[int]:
        """Current DMX values."""
        return self._current_values

    @current_values.setter
    def current_values(self, values: list[int]) -> None:
        self._last_values = self._current_values
        self._current_values = values
        self.new_value.emit()

    def trend(self, index: int) -> int:
        """DMX value change since last update."""
        return self._current_values[index] - self._last_values[index]
