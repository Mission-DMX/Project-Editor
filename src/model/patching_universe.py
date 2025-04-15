# coding=utf-8
"""universe for Patching"""
import proto.UniverseControl_pb2
from model.patching_channel import PatchingChannel


class PatchingUniverse:
    """Universe for Patching"""

    def __init__(self, universe_proto: proto.UniverseControl_pb2.Universe) -> None:
        self._universe_proto: proto.UniverseControl_pb2 = universe_proto
        self._patching: list[PatchingChannel] = [PatchingChannel(channel_address) for channel_address in
                                                 range(512)]

    @property
    def universe_proto(self) -> proto.UniverseControl_pb2.Universe:
        """property oy universeProto"""
        return self._universe_proto

    @universe_proto.setter
    def universe_proto(self, proto_: proto.UniverseControl_pb2.Universe) -> None:
        self._universe_proto = proto_

    @property
    def patching(self) -> list[PatchingChannel]:
        """List of all 512 patching channels belonging to the Universe"""
        return self._patching

    @property
    def name(self) -> str:
        """Human-readable name for the universe."""
        return f"Universe {self.universe_proto.id}"

    @property
    def description(self) -> str:
        """Human-readable description for the universe."""
        return self.name
