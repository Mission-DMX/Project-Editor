"""Channel of a fixture."""

from enum import IntFlag
from typing import Final

from PySide6 import QtCore


class FixtureChannelType(IntFlag):
    """Channels Types of a fixture."""

    UNDEFINED = 0
    RED = 1
    GREEN = 2
    BLUE = 4
    WHITE = 8
    AMBER = 16
    UV = 32

    POSITION = 64
    PAN = 128
    TILT = 256
    ROTATION = 512
    SPEED = 1024
    # TODO vielleicht als enum


class FixtureChannel:
    """Channel of a fixture."""

    updated: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, name: str) -> None:
        """Channel of a fixture."""
        self._name: Final[str] = name
        self._type: Final[FixtureChannelType] = self._get_channel_type_from_string()
        self._ignore_black = True

    @property
    def name(self) -> str:
        """Name of the channel."""
        return self._name

    @property
    def type(self) -> FixtureChannelType:
        """Type of the channel."""
        return self._type

    @property
    def type_as_list(self) -> list[FixtureChannelType]:
        """Export the Fixture Channel Types as a list."""
        return [flag for flag in type(self._type) if flag in self._type]

    @property
    def ignore_black(self) -> bool:
        """Ignore this channel blackout."""
        return self._ignore_black

    @ignore_black.setter
    def ignore_black(self, ignore_black: bool) -> None:
        self._ignore_black = ignore_black

    def _get_channel_type_from_string(self) -> FixtureChannelType:
        """Generate channel types from a string."""
        types: FixtureChannelType = FixtureChannelType.UNDEFINED
        # TODO vielleicht aus OFL sauber extrahieren
        for channel_type in FixtureChannelType:
            if str(channel_type.name).lower() in self._name.lower():
                types &= channel_type
                if channel_type in (FixtureChannelType.PAN, FixtureChannelType.TILT):
                    types &= FixtureChannelType.POSITION

        return types
