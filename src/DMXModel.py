# coding=utf-8
"""Provides data structures with accessors and modifiers for DMX"""

from PySide6 import QtCore

import proto.UniverseControl_pb2
from ofl.fixture import UsedFixture, Mode


class Channel(QtCore.QObject):
    """Basic dmx channel with 256 values"""

    updated: QtCore.Signal = QtCore.Signal(int)

    def __init__(self, channel_address: int):
        """Constructs a channel."""
        super().__init__()
        if 0 > channel_address or channel_address > 511:
            raise ValueError(f"Tried to create a channel with address {channel_address}")
        self._address: int = channel_address
        self._value: int = 0

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

    @property
    def value(self) -> int:
        """The current value of the channel"""
        return self._value

    @value.setter
    def value(self, value: int):
        """Updates the value of the channel.
                        Must be between 0 and 255.

                        Raises:
                            ValueError: The value is below 0 or above 255.
                        """
        if 0 > value or value > 255:
            raise ValueError(f"Tried to set channel {self._address} to {value}.")
        self._value = value
        self.updated.emit(value)


class PatchingChannel(QtCore.QObject):
    """Channels for patching to reduce redundancy over scenes"""

    def __init__(self, channel_address: int, color: str):
        """Constructs a patching channel."""
        super().__init__()
        if 0 > channel_address or channel_address > 511:
            raise ValueError(f"Tried to create a channel with address {channel_address}")
        self._address: int = channel_address
        self._fixture: UsedFixture = UsedFixture("Empty", "", set(), "", Mode(channels=["none"], shortName="", name=""))
        self._fixture_channel: int = 0
        self._color: str = color

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

    @property
    def fixture(self) -> UsedFixture:
        """The fixture of the channel"""
        return self._fixture

    @fixture.setter
    def fixture(self, fixture: UsedFixture):
        self._fixture = fixture

    @property
    def fixture_channel(self) -> str:
        """The use of this channel in Fixture"""
        return self._fixture.mode['channels'][self._fixture_channel]

    @fixture_channel.setter
    def fixture_channel(self, fixture_channel: int):
        self._fixture_channel = fixture_channel

    @property
    def color(self) -> str:
        """color of the fixture in PatchPlan"""
        return self._color

    @color.setter
    def color(self, color: str):
        self._color = color


class Device:
    """A DMX device"""

    def __init__(self, name: str):
        self._name: str = name

    @property
    def name(self) -> str:
        """ID of the dmx device"""
        return self._name


class Universe:
    """DMX universe with 512 channels"""

    def __init__(self, universe_proto: proto.UniverseControl_pb2.Universe,
                 patching_channels: list[PatchingChannel] = None):
        self._universe_proto: proto.UniverseControl_pb2 = universe_proto
        if patching_channels is None:
            patching_channels = [PatchingChannel(channel_address, "#000000") for channel_address in range(512)]
        self._patching: list[PatchingChannel] = patching_channels
        self._channels: list[Channel] = [Channel(channel_address) for channel_address in range(512)]

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """property oy universeProto"""
        return self._universe_proto

    @property
    def channels(self) -> list[Channel]:
        """List of all 512 dmx channels belonging to the Universe"""
        return self._channels

    @property
    def patching(self) -> list[PatchingChannel]:
        """List of all 512 patching channels belonging to the Universe"""
        return self._patching


class Filter:
    """Filter
    TODO implement
    """

    def __init__(self):
        pass
