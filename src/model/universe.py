# coding=utf-8
"""DMX Universe"""
import proto.UniverseControl_pb2
from model.channel import Channel
from model.patching_channel import PatchingChannel
from model.patching_universe import PatchingUniverse


class Universe:
    """DMX universe with 512 channels"""

    def __init__(self, patching_universe: PatchingUniverse):
        self._patching_universe: PatchingUniverse = patching_universe
        self._channels: list[Channel] = [Channel(channel_address) for channel_address in range(512)]
        self._name = f"Universe {self.universe_proto.id}"
        self._description = self.name

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """property oy universeProto"""
        return self._patching_universe.universe_proto

    @property
    def channels(self) -> list[Channel]:
        """List of all 512 dmx channels belonging to the Universe"""
        return self._channels

    @property
    def patching(self) -> list[PatchingChannel]:
        """List of all 512 patching channels belonging to the Universe"""
        return self._patching_universe.patching

    @property
    def id(self) -> int:
        """id of the universe"""
        return self._patching_universe.universe_proto.id

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
        if self._patching_universe.universe_proto.remote_location.ip_address != "":
            return self._patching_universe.universe_proto.remote_location
        if self._patching_universe.universe_proto.ftdi_dongle.vendor_id != "":
            return self._patching_universe.universe_proto.ftdi_dongle

        return self._patching_universe.universe_proto.physical_location
