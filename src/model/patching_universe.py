# coding=utf-8
"""universe for Patching"""
import proto
from model.patching_channel import PatchingChannel


class PatchingUniverse:
    """Universe for Patching"""

    def __init__(self, universe_proto: proto.UniverseControl_pb2.Universe,
                 patching_channels: list[PatchingChannel] = None) -> None:
        self._universe_proto: proto.UniverseControl_pb2 = universe_proto
        if patching_channels is None:
            patching_channels = [PatchingChannel(channel_address, "#FFFFFF") for channel_address in range(512)]
        self._patching: list[PatchingChannel] = patching_channels

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """property oy universeProto"""
        return self._universe_proto

    @property
    def patching(self) -> list[PatchingChannel]:
        """List of all 512 patching_mode channels belonging to the Universe"""
        return self._patching

    @property
    def name(self) -> str:
        """Human-readable name for the universe."""
        return f"Universe {self.universe_proto.id}"

    @property
    def description(self) -> str:
        """Human-readable description for the universe."""
        return self.name
