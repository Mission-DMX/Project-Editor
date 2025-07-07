"""Fixture Definitions from OFL """
from __future__ import annotations

import json
import random
from collections import defaultdict
from collections.abc import Sequence
from enum import Enum, IntFlag
from logging import getLogger
from typing import TYPE_CHECKING, Final, NotRequired, TypedDict, Any
from uuid import UUID, uuid4

import numpy as np
from PySide6 import QtCore
from numpy.typing import NDArray

from model.patching.fixture_channel import FixtureChannel, FixtureChannelType

if TYPE_CHECKING:
    from model import BoardConfiguration

logger = getLogger(__file__)


class Category(Enum):
    """Category of Fixtures"""
    BARREL_SCANNER = "Barrel Scanner"
    BLINDER = "Blinder"
    COLOR_CHANGER = "Color Changer"
    DIMMER = "Dimmer"
    EFFECT = "Effect"
    FAN = "Fan"
    FLOWER = "Flower"
    HAZER = "Hazer"
    LASER = "Laser"
    MATRIX = "Matrix"
    MOVING_HEAD = "Moving Head"
    PIXEL_BAR = "Pixel Bar"
    SCANNER = "Scanner"
    SMOKE = "Smoke"
    STAND = "Stand"
    STROBE = "Strobe"
    OTHER = "Other"


# class Capabilities:
#    dmxRange: tuple[int, int]


# class Channel(TypedDict):
#    defaultValue: str
#    highlightValue: str
#    capabilities: list[Capabilities]


class Mode(TypedDict):
    """ possible Modes of a fixture"""
    name: str
    shortName: str
    #    rdmPersonalityIndex: int
    #    physical: Physical
    channels: list[str]


class Fixture(TypedDict):
    """a Fixture from OFL"""
    name: str
    shortName: NotRequired[str]
    categories: set[Category]
    #    meta: MetaData
    comment: NotRequired[str]
    #    links: Links
    #    helpWanted
    #    rdm
    #    physical
    #    matrix: Matrix
    #    wheels
    #    availableChannels
    #    templateChannels
    modes: list[Mode]
    fileName: str


class ColorSupport(IntFlag):
    """Color Support of Fixture"""
    NO_COLOR_SUPPORT = 0
    COLD_AND_WARM_WHITE = 1
    HAS_RGB_SUPPORT = 2
    HAS_WHITE_SEGMENT = 4
    HAS_AMBER_SEGMENT = 8
    HAS_UV_SEGMENT = 16

    def __str__(self):
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


def load_fixture(file) -> Fixture:
    """load fixture from OFL json"""
    with open(file, "r", encoding='UTF-8') as f:
        ob: dict[str, Any] = json.load(f)
    return Fixture(name=ob["name"], comment=try_load(ob, "comment"), shortName=try_load(ob, "shortName"),
                   categories=ob["categories"] if "categories" in ob else set(),
                   modes=ob["modes"] if "modes" in ob else [], fileName=file.split("/fixtures/")[1])


def try_load(ob: dict[str, str], name: str) -> str:
    """ try to load not required JSON parts"""
    try:
        return ob[name]
    except KeyError:
        return ""


class UsedFixture(QtCore.QObject):
    """ Fixture in use with a specific mode"""
    static_data_changed: QtCore.Signal = QtCore.Signal()

    def __init__(self, board_configuration: BoardConfiguration, fixture: Fixture, mode_index: int,
                 parent_universe: int,
                 start_index: int, uuid: UUID = None, color: str = None):
        super().__init__()
        self._board_configuration: Final[BoardConfiguration] = board_configuration
        self._fixture: Final[Fixture] = fixture
        self._uuid: Final[UUID] = uuid if uuid else uuid4()

        self._start_index: int = start_index
        self._mode_index: int = mode_index
        self._universe_id: int = parent_universe

        channels, segment_map, color_support = self._generate_fixture_channels()

        self._fixture_channels: Final[list[FixtureChannel]] = channels
        self._segment_map: dict[FixtureChannelType, NDArray[np.int_]] = segment_map
        self._color_support: Final[ColorSupport] = color_support

        self._color_on_stage: str = color if color else "#" + ''.join(
            [random.choice('0123456789ABCDEF') for _ in range(6)])
        self._name_on_stage: str = self.short_name if self.short_name else self.name

        self.parent_universe: int = parent_universe
        self._board_configuration.broadcaster.add_fixture.emit(self)

    @property
    def uuid(self) -> UUID:
        """uuid of the fixture"""
        return self._uuid

    @property
    def name(self) -> str:
        """name of the fixture"""
        return self._fixture.get("name")

    @property
    def short_name(self) -> str:
        """short name of the fixture"""
        return self._fixture.get("shortName")

    @property
    def comment(self) -> str:
        """comment of the fixture"""
        return self._fixture.get("comment")

    @property
    def mode(self) -> Mode:
        """mode of the fixture"""
        return self._fixture.get("modes")[self._mode_index]

    @property
    def start_index(self) -> int:
        """start index of the fixture in the universe"""
        return self._start_index

    @property
    def fixture_file(self) -> str:
        """file of the fixture"""
        return self._fixture.get("fileName")

    @property
    def mode_index(self) -> int:
        """index of the mode in the fixture"""
        return self._mode_index

    @property
    def universe_id(self) -> int:
        """id of the universe"""
        return self._universe_id

    @universe_id.setter
    def universe_id(self, universe_id: int):
        self._universe_id = universe_id

    @property
    def channel_length(self) -> int:
        """get the number of channels in the fixture"""
        return len(self._fixture_channels)

    @property
    def channel_indexes(self) -> list[int]:
        """index of the channels in the fixture"""
        return list(range(self._start_index, self._start_index + len(self._fixture_channels)))

    @property
    def fixture_channels(self) -> tuple[FixtureChannel, ...]:
        """fixture channels of the fixture"""
        return tuple(self._fixture_channels)

    @property
    def color_on_stage(self) -> str:
        """color of the fixture on stage"""
        return self._color_on_stage

    @color_on_stage.setter
    def color_on_stage(self, color: str):
        self._color_on_stage = color
        self.static_data_changed.emit()

    @property
    def name_on_stage(self) -> str:
        """name of the fixture on stage"""
        return self._name_on_stage

    @name_on_stage.setter
    def name_on_stage(self, name: str):
        self._name_on_stage = name
        self.static_data_changed.emit()

    @property
    def color_support(self) -> ColorSupport:
        """color support of the fixture"""
        return self._color_support

    def get_segment_in_universe_by_type(self, segment_type: FixtureChannelType) -> Sequence[int]:
        """get a segment by type"""
        return tuple((self._segment_map[segment_type] + self.start_index).tolist())

    def _generate_fixture_channels(self) -> tuple[
        list[FixtureChannel], dict[FixtureChannelType, NDArray[np.int_]], ColorSupport]:

        segment_map: dict[FixtureChannelType, list[int]] = defaultdict(list)
        fixture_channels: list[FixtureChannel] = []

        for index, channel_name in enumerate(self.mode["channels"]):
            channel = FixtureChannel(channel_name)
            fixture_channels.append(channel)
            for channel_type in channel.type_as_list:
                segment_map[channel_type].append(index)

        found_color = ColorSupport.NO_COLOR_SUPPORT
        if all(segment_map[t] for t in (FixtureChannelType.RED, FixtureChannelType.GREEN, FixtureChannelType.BLUE)):
            found_color |= ColorSupport.HAS_RGB_SUPPORT
        if segment_map[FixtureChannelType.UV]:
            found_color |= ColorSupport.HAS_UV_SEGMENT
        if segment_map[FixtureChannelType.AMBER]:
            found_color |= ColorSupport.HAS_AMBER_SEGMENT
        if segment_map[FixtureChannelType.WHITE]:
            found_color |= ColorSupport.HAS_WHITE_SEGMENT

        return fixture_channels, {key: np.array(segment_map[key], dtype=np.int_) for key in
                                  FixtureChannelType}, found_color

    def get_fixture_channel(self, index: int) -> FixtureChannel:
        """get a fixture channel by index"""
        return self._fixture_channels[index]


def make_used_fixture(board_configuration: BoardConfiguration, fixture: Fixture, mode_index: int, universe_id: int,
                      start_index: int) -> UsedFixture:
    """generate a new Used Fixture from a fixture"""
    return UsedFixture(board_configuration, fixture, mode_index, universe_id, start_index)
