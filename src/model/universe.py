# coding=utf-8
"""DMX Universe"""
import proto.UniverseControl_pb2
from model.channel import Channel
from model.patching_channel import PatchingChannel


class Universe:
    """DMX universe with 512 channels"""

    def __init__(self, universe_proto: proto.UniverseControl_pb2.Universe,
                 patching_channels: list[PatchingChannel] = None):
        self._universe_proto: proto.UniverseControl_pb2 = universe_proto
        if patching_channels is None:
            patching_channels = [PatchingChannel(channel_address, "#FFFFFF") for channel_address in range(512)]
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
        
