# coding=utf-8
"""Provides data structures with accessors and modifiers for DMX"""
from PySide6 import QtCore

import proto.UniverseControl_pb2


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
        self._device: Device = Device("<empty>")

    @property
    def address(self) -> int:
        """Address of the channel. 0-indexed"""
        return self._address

    @property
    def value(self) -> int:
        """The current value of the channel"""
        return self._value

    @property
    def device(self):
        return self._device

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
    def __init__(self, universe_proto: proto.UniverseControl_pb2.Universe):
        self._universe_proto = universe_proto
        self._channels: list[Channel] = [Channel(channel_address) for channel_address in range(512)]
        self._devices: list[Device] = []

    @property
    def address(self) -> int:
        """ID of the dmx universe. 0-indexed"""
        return self._universe_proto.id

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """property oy universeProto"""
        return self._universe_proto

    @property
    def channels(self) -> list[Channel]:
        """List of all 512 dmx channels belonging to the channel"""
        return self._channels


class Scene:
    """Scene
    TODO implement
    """

    def __init__(self):
        pass


class Filter:
    """Filter
    TODO implement
    """

    def __init__(self):
        pass
