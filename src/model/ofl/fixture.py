# coding=utf-8
"""Fixture Definitions from OFL."""

from __future__ import annotations

import json
import os
import random
from collections import defaultdict
from enum import IntFlag
from logging import getLogger
from typing import TYPE_CHECKING, Final
from uuid import UUID, uuid4

import numpy as np
from PySide6 import QtCore

from model.ofl.ofl_fixture import FixtureMode, MatrixChannelInsert, OflFixture
from model.patching.fixture_channel import FixtureChannel, FixtureChannelType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from model import BoardConfiguration

logger = getLogger(__name__)


class ColorSupport(IntFlag):
    """Color Support of fixture."""

    NO_COLOR_SUPPORT = 0
    COLD_AND_WARM_WHITE = 1
    HAS_RGB_SUPPORT = 2
    HAS_WHITE_SEGMENT = 4
    HAS_AMBER_SEGMENT = 8
    HAS_UV_SEGMENT = 16

    def __str__(self) -> str:
        """Generate human-readable channel color support representation."""
        if self == ColorSupport.NO_COLOR_SUPPORT:
            return "No Color Support"
        s = []
        if (self & ColorSupport.COLD_AND_WARM_WHITE) > 0:
            s.append("CW/WW")
        if (self & ColorSupport.HAS_RGB_SUPPORT) > 0:
            s.append("RGB")
        if (self & ColorSupport.HAS_WHITE_SEGMENT) > 0:
            s.append("W")
        if (self & ColorSupport.HAS_AMBER_SEGMENT) > 0:
            s.append("A")
        if (self & ColorSupport.HAS_UV_SEGMENT) > 0:
            s.append("U")
        return "+".join(s)


def load_fixture(file: str) -> OflFixture | None:
    """Load fixture from OFL JSON."""
    if not os.path.isfile(file):
        logger.error("Fixture definition %s not found.", file)
        return None
    with open(file, "r", encoding="UTF-8") as f:
        ob: dict = json.load(f)
    ob.update({"fileName": file.split("\\fixtures\\")[0]})
    return OflFixture.model_validate(ob)


class UsedFixture(QtCore.QObject):
    """Fixture in use with a specific mode."""

    static_data_changed: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        board_configuration: BoardConfiguration,
        fixture: OflFixture,
        mode_index: int,
        parent_universe: int,
        start_index: int,
        uuid: UUID | None = None,
        color: str | None = None,
    ) -> None:
        """Instantiate a UsedFixture object.

        Args:
            board_configuration: The show model
            fixture: The base fixture definition
            mode_index: The fixture mode to use
            parent_universe: The parent universe
            start_index: The first channels address
            uuid: The UUID of the fixture instance
            color: The color of the fixture in the patching view

        """
        super().__init__()
        self._board_configuration: Final[BoardConfiguration] = board_configuration
        self._fixture: Final[OflFixture] = fixture
        self._uuid: Final[UUID] = uuid if uuid else uuid4()

        self._start_index: int = start_index
        self._mode_index: int = mode_index
        self._universe_id: int = parent_universe

        channels, segment_map, color_support = self._generate_fixture_channels()

        self._fixture_channels: Final[list[FixtureChannel]] = channels
        self._segment_map: dict[FixtureChannelType, NDArray[np.int_]] = segment_map
        self._color_support: Final[ColorSupport] = color_support

        self._color_on_stage: str = (
            color if color else "#" + "".join([random.choice("0123456789ABCDEF") for _ in range(6)])  # noqa: S311 not a secret
        )
        self._name_on_stage: str = self.short_name if self.short_name else self.name

        self.parent_universe: int = parent_universe
        self._board_configuration.broadcaster.add_fixture.emit(self)

    @property
    def uuid(self) -> UUID:
        """UUID of the fixture."""
        return self._uuid

    @property
    def power(self) -> float:
        """Fixture maximum continuous power draw (not accounting for capacitor charging as well as lamp warmup) in W."""
        return self._fixture.physical.power

    @property
    def name(self) -> str:
        """Name of theFixture."""
        return self._fixture.name

    @property
    def short_name(self) -> str:
        """Short name of theFixture."""
        return self._fixture.shortName

    @property
    def comment(self) -> str:
        """Comment of theFixture."""
        return self._fixture.comment

    @property
    def mode(self) -> FixtureMode:
        """Mode of theFixture."""
        return self._fixture.modes[self._mode_index]

    @property
    def start_index(self) -> int:
        """Start index of theFixture in the Universe indexed by 0."""
        return self._start_index

    @property
    def fixture_file(self) -> str:
        """File of the fixture."""
        return self._fixture.fileName

    @property
    def mode_index(self) -> int:
        """Index of the mode in the fixture."""
        return self._mode_index

    @property
    def universe_id(self) -> int:
        """Id of the universe for the fixture."""
        return self._universe_id

    @universe_id.setter
    def universe_id(self, universe_id: int) -> None:
        self._universe_id = universe_id

    @property
    def channel_length(self) -> int:
        """Number of channels of the fixture."""
        return len(self._fixture_channels)

    @property
    def channel_indexes(self) -> list[int]:
        """Index of the channels in the fixture."""
        return list(range(self._start_index, self._start_index + len(self._fixture_channels)))

    @property
    def fixture_channels(self) -> tuple[FixtureChannel, ...]:
        """Fixture channels of the fixture."""
        return tuple(self._fixture_channels)

    @property
    def color_on_stage(self) -> str:
        """Color of the fixture on stage."""
        return self._color_on_stage

    @color_on_stage.setter
    def color_on_stage(self, color: str) -> None:
        self._color_on_stage = color
        self.static_data_changed.emit()

    @property
    def name_on_stage(self) -> str:
        """Name of the fixture on stage."""
        return self._name_on_stage

    @name_on_stage.setter
    def name_on_stage(self, name: str) -> None:
        self._name_on_stage = name
        self.static_data_changed.emit()

    @property
    def color_support(self) -> ColorSupport:
        """Color support of the fixture."""
        return self._color_support

    def get_segment_in_universe_by_type(self, segment_type: FixtureChannelType) -> Sequence[int]:
        """Get a segment by type."""
        return tuple((self._segment_map[segment_type] + self.start_index).tolist())

    def _generate_fixture_channels(
        self,
    ) -> tuple[list[FixtureChannel], dict[FixtureChannelType, NDArray[np.int_]], ColorSupport]:
        segment_map: dict[FixtureChannelType, list[int]] = defaultdict(list)
        fixture_channels: list[FixtureChannel] = []

        def append_channel(cn: str, i: int) -> None:
            channel = FixtureChannel(cn)
            fixture_channels.append(channel)
            for channel_type in channel.type_as_list:
                segment_map[channel_type].append(i)

        index = 0
        for channel_name in self.mode.channels:
            if isinstance(channel_name, MatrixChannelInsert):
                if isinstance(channel_name.repeatFor, list):
                    repetition_list = channel_name.repeatFor
                else:
                    repetition_list = self._fixture.matrix.generate_repetition_list(channel_name.repeatFor)
                for repeated_name in repetition_list:
                    for template_name in channel_name.templateChannels:
                        append_channel(template_name.replace("$pixelKey", "{}").format(repeated_name), index)
                        index += 1
            else:
                append_channel(channel_name if channel_name is not None else "", index)
                index += 1

        found_color = ColorSupport.NO_COLOR_SUPPORT
        if all(segment_map[t] for t in (FixtureChannelType.RED, FixtureChannelType.GREEN, FixtureChannelType.BLUE)):
            found_color |= ColorSupport.HAS_RGB_SUPPORT
        if segment_map[FixtureChannelType.UV]:
            found_color |= ColorSupport.HAS_UV_SEGMENT
        if segment_map[FixtureChannelType.AMBER]:
            found_color |= ColorSupport.HAS_AMBER_SEGMENT
        if segment_map[FixtureChannelType.WHITE]:
            found_color |= ColorSupport.HAS_WHITE_SEGMENT

        return (
            fixture_channels,
            {key: np.array(segment_map[key], dtype=np.int_) for key in FixtureChannelType},
            found_color,
        )

    def get_fixture_channel(self, index: int) -> FixtureChannel:
        """Get a fixture channel by index."""
        return self._fixture_channels[index]

    def __str__(self) -> str:
        """Get a human-readable description of the fixture in the show file."""
        return f"Fixture {self.name_on_stage or self.name} at {self.parent_universe}/{self.start_index}"


def make_used_fixture(
    board_configuration: BoardConfiguration, fixture: OflFixture, mode_index: int, universe_id: int, start_index: int
) -> UsedFixture:
    """Generate a new Used Fixture from a oflFixture."""
    return UsedFixture(board_configuration, fixture, mode_index, universe_id, start_index)
