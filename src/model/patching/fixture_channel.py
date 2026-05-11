"""Channels of a Fixture."""

from __future__ import annotations

from enum import IntFlag
from logging import getLogger
from typing import TYPE_CHECKING, Final

from PySide6 import QtCore

from model.ofl.ofl_fixture import CapabilityType

if TYPE_CHECKING:
    from model.ofl.ofl_fixture import ChannelTemplate, OflFixture

logger = getLogger(__name__)


class FixtureChannelType(IntFlag):
    """Types of channels of a fixture."""

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
    COLORWHEEL = 2048
    # TODO vielleicht als enum


class FixtureChannel:
    """A channel of a fixture."""

    updated: QtCore.Signal(int) = QtCore.Signal(int)

    def __init__(self, name: str, parent_fixture_template: OflFixture) -> None:
        """Initialize a fixture channel."""
        self._name: Final[str] = name
        self._channel_template: Final[ChannelTemplate | None] = parent_fixture_template.availableChannels.get(self.name)
        self._type: Final[FixtureChannelType] = self._get_channel_type_from_template_or_string()
        self._ignore_black = True

    @property
    def name(self) -> str:
        """Returns the name of the channel."""
        return self._name

    @property
    def type(self) -> FixtureChannelType:
        """Returns the channel type."""
        return self._type

    @property
    def type_as_list(self) -> list[FixtureChannelType]:
        """Export the Fixture Channel Types as a list."""
        return [flag for flag in type(self._type) if flag in self._type]

    @property
    def ignore_black(self) -> bool:
        """Ignore this channel blackout."""
        return self._ignore_black

    @property
    def channel_template(self) -> ChannelTemplate | None:
        """Returns the channel template."""
        return self._channel_template

    @ignore_black.setter
    def ignore_black(self, ignore_black: bool) -> None:
        self._ignore_black = ignore_black

    def _get_channel_type_from_template_or_string(self) -> FixtureChannelType:
        """Returns the channel type."""
        types: FixtureChannelType = FixtureChannelType.UNDEFINED

        name = self._name.lower()

        if self._channel_template:
            for capability in self._channel_template.get_capabilities():
                match capability.type:
                    case CapabilityType.COLOR_INTENSITY:
                        if "red" in name:
                            types |= FixtureChannelType.RED
                        elif "green" in name:
                            types |= FixtureChannelType.GREEN
                        elif "blue" in name:
                            types |= FixtureChannelType.BLUE
                        elif "white" in name:
                            types |= FixtureChannelType.WHITE
                        elif "amber" in name:
                            types |= FixtureChannelType.AMBER
                        elif "uv" in name:
                            types |= FixtureChannelType.UV
                    case CapabilityType.PAN:
                        types |= FixtureChannelType.PAN
                    case CapabilityType.TILT:
                        types |= FixtureChannelType.TILT
                    case CapabilityType.ROTATION:
                        types |= FixtureChannelType.ROTATION
                    case CapabilityType.SPEED | CapabilityType.EFFECT_SPEED | CapabilityType.STROBE_SPEED | \
                         CapabilityType.PAN_TILT_SPEED:
                        types |= FixtureChannelType.SPEED
                    case CapabilityType.WHEEL_SLOT:
                        if "color" in name:
                            types |= FixtureChannelType.COLORWHEEL
                    case _:
                        continue
            return types

        for channel_type in FixtureChannelType:
            if str(channel_type.name).lower() in name:
                types &= channel_type
                if channel_type in (FixtureChannelType.PAN, FixtureChannelType.TILT):
                    types &= FixtureChannelType.POSITION

        return types
