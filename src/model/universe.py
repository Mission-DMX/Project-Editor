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
        """List of all 512 patching channels belonging to the Universe"""
        return self._patchingUniverse.patching

    @property
    def name(self) -> str:
        """Human-readable name for the universe."""
        return f"Universe {self.universe_proto.id}"

    @property
    def description(self) -> str:
        """Human-readable description for the universe."""
        return self.name

