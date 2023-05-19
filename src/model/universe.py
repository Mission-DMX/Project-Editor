# coding=utf-8
"""DMX Universe"""
import proto.UniverseControl_pb2
from model.channel import Channel
from model.patching_channel import PatchingChannel
from model.patching_universe import PatchingUniverse


class Universe:
    """DMX universe with 512 channels"""

    def __init__(self, patching_universe: PatchingUniverse):
        self._patchingUniverse: PatchingUniverse = patching_universe
        self._channels: list[Channel] = [Channel(channel_address) for channel_address in range(512)]

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """property oy universeProto"""
        return self._patchingUniverse.universe_proto

    @property
    def channels(self) -> list[Channel]:
        """List of all 512 dmx channels belonging to the Universe"""
        return self._channels

    @property
    def patching(self) -> list[PatchingChannel]:
        """List of all 512 patching_mode channels belonging to the Universe"""
        return self._patchingUniverse.patching

    @property
    def id(self) -> int:
        """Id of the universe"""
        return self._patchingUniverse.universe_proto.id

    @property
    def name(self) -> str:
        """Human-readable name for the universe."""
        if self._name is None:
            self._name = f"Universe {self.universe_proto.id}"
        return self._name
    
    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def description(self) -> str:
        """Human-readable description for the universe."""
        if self._description is None:
            self._description = self.name()
        return self._description
    
    @description.setter
    def description(self, description: str):
        self._description = description

    @property
    def location(self) -> int | proto.UniverseControl_pb2.Universe.ArtNet | proto.UniverseControl_pb2.Universe.USBConfig:
        #if self._universe_proto.physical_location:
        #    return self._universe_proto.physical_location
        #if self._universe_proto.remote_location:
        #    return self._universe_proto.remote_location
        #if self._universe_proto.ftdi_dongle:
        return self._universe_proto.ftdi_dongle
        
