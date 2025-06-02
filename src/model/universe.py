# coding=utf-8
"""DMX Universe"""
from typing import Final

import proto.UniverseControl_pb2
from model.channel import Channel


class Universe:
    """DMX universe with 512 channels"""

    def __init__(self, universe_proto: proto.UniverseControl_pb2.Universe):
        self._universe_proto: proto.UniverseControl_pb2.Universe = universe_proto
        self._channels: Final[list[Channel]] = [Channel(channel_address) for channel_address in range(512)]

        self._name = f"Universe {self.universe_proto.id + 1}"
        self._description = self.name

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """the UniverseProto of the Universe"""
        return self._universe_proto

    @universe_proto.setter
    def universe_proto(self, proto_: proto.UniverseControl_pb2.Universe) -> None:
        self._universe_proto = proto_

    @property
    def channels(self) -> list[Channel]:
        """List of all 512 dmx channels belonging to the Universe"""
        return self._channels

    @property
    def id(self) -> int:
        """id of the universe"""
        return self._universe_proto.id

    @property
    def name(self) -> str:
        """Human-readable name for the universe."""
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def description(self) -> str:
        """Human-readable description for the universe."""
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description

    @property
    def location(
            self) -> int | proto.UniverseControl_pb2.Universe.ArtNet | proto.UniverseControl_pb2.Universe.USBConfig:
        """network location"""
        if self._universe_proto.remote_location.ip_address != "":
            return self._universe_proto.remote_location
        if self._universe_proto.ftdi_dongle.vendor_id != "":
            return self._universe_proto.ftdi_dongle

        return self._universe_proto.physical_location
