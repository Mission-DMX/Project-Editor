# coding=utf-8
"""Fixture Definitions from OFL """
import json
from enum import Enum, IntFlag
from typing import TypedDict, NotRequired, TYPE_CHECKING

from logging import getLogger
logger = getLogger(__file__)

if TYPE_CHECKING:
    from model.patching_channel import PatchingChannel


class Category(Enum):
    """Category of Fixtures"""
    "Barrel Scanner"
    "Blinder"
    "Color Changer"
    "Dimmer"
    "Effect"
    "Fan"
    "Flower"
    "Hazer"
    "Laser"
    "Matrix"
    "Moving Head"
    "Pixel Bar"
    "Scanner"
    "Smoke"
    "Stand"
    "Strobe"
    "Other"


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
    f = open(file)
    ob: json = json.load(f)
    return Fixture(name=ob["name"], comment=try_load(ob, "comment"), shortName=try_load(ob, "shortName"),
                   categories=ob["categories"] if "categories" in ob else [], modes=ob["modes"] if "modes" in ob else [], fileName=file.split("/fixtures/")[1])


def try_load(ob: json, name: object) -> str:
    """ try to load not required json parts"""
    try:
        return ob[name]
    except KeyError:
        return ""


class UsedFixture:
    """ Fixture in use with a specific mode"""

    def __init__(self, name: str, short_name: str, categories: set[Category], comment: str, mode: Mode,
                 fixture_file: str, mode_index: int, parent_universe: int) -> None:
        self.name: str = name
        self.short_name: str = short_name
        self.categories: set[Category] = categories
        self.comment: str = comment
        self.mode: Mode = mode
        self.parent_universe: int = parent_universe
        self._channels: list["PatchingChannel"] = []
        self.fixture_file: str = fixture_file
        self.mode_index: int = mode_index

        self.red_segments: list["PatchingChannel"] = []
        self.blue_segments: list["PatchingChannel"] = []
        self.green_segments: list["PatchingChannel"] = []
        self.white_segments: list["PatchingChannel"] = []
        self.amber_segments: list["PatchingChannel"] = []
        self.uv_segments: list["PatchingChannel"] = []

        self.position_channels: list["PatchingChannel"] = []
        self.pan_channels: list["PatchingChannel"] = []
        self.tilt_channels: list["PatchingChannel"] = []
        self.animation_speed_channels: list["PatchingChannel"] = []

    def update_segments(self):
        self.red_segments.clear()
        self.blue_segments.clear()
        self.green_segments.clear()
        self.white_segments.clear()
        self.amber_segments.clear()
        self.uv_segments.clear()

        for f in self.channels:
            # TODO looking at the fixture data this might work well for led based color changers.
            #  Yet, we need to support color wheels as well. One option would be to check for the "capability": {
            #         "type": "ColorIntensity",
            #         "color": "Red"
            #       }
            #  Data of a fixture channel.
            if not isinstance(f.fixture_channel, str):
                continue
            found_color_hints: int = 0
            if "red" in f.fixture_channel.lower():
                self.red_segments.append(f)
                found_color_hints += 1
            if "green" in f.fixture_channel.lower():
                self.green_segments.append(f)
                found_color_hints += 1
            if "blue" in f.fixture_channel.lower():
                self.blue_segments.append(f)
                found_color_hints += 1
            if "white" in f.fixture_channel.lower():
                self.white_segments.append(f)
                found_color_hints += 1
                # TODO we also need to append this in case the fixture does not have rgb support but multiple white
                #  segments (such as a LED blinder)
            if "uv" in f.fixture_channel.lower():
                self.uv_segments.append(f)
                found_color_hints += 1
            if "amber" in f.fixture_channel.lower():
                self.amber_segments.append(f)
                found_color_hints += 1
            if found_color_hints > 1:
                logger.warning("Associated %s/%s:%s in multiple color segments.",
                               str(self.parent_universe), str(f.address), f.fixture_channel)
        # TODO discussion: integration of fixture groups would be most straight forward if they would be represented as
        #  an inheritance of UsedFixture, representing their individual lamps as segments of the group. This way we
        #  would not need to implement special cases everywhere where this information is accessed.

    def find_position_channels(self):
        self.position_channels.clear()
        self.pan_channels.clear()
        self.tilt_channels.clear()
        self.animation_speed_channels.clear()
        for f in self.channels:
            channel_name = f.fixture_channel.lower()
            if "pan" in channel_name:
                self.position_channels.append(f)
                if "speed" in channel_name:
                    self.animation_speed_channels.append(f)
                    continue
                else:
                    self.pan_channels.append(f)
            if "tilt" in channel_name:
                self.position_channels.append(f)
                if "speed" in channel_name:
                    self.animation_speed_channels.append(f)
                    continue
                else:
                    self.tilt_channels.append(f)
            if "rotation" in channel_name:
                # This will also catch lense and gobo rotations
                self.position_channels.append(f)

    def copy(self):
        """
        This method clones the used fixture entry, except for the occupied channels
        """
        return UsedFixture(self.name, self.short_name, self.categories,
                           self.comment, self.mode, self.fixture_file, self.mode_index, self.parent_universe)
        # we do not need to copy the segment data as it is deduced from the channels data

    @property
    def channels(self) -> list["PatchingChannel"]:
        self._channels.sort(key=lambda x: x.address)
        return self._channels

    def color_support(self) -> ColorSupport:
        found_color = ColorSupport.NO_COLOR_SUPPORT

        has_red = len(self.red_segments) > 0
        has_green = len(self.green_segments) > 0
        has_blue = len(self.blue_segments) > 0
        has_white = len(self.white_segments) > 0
        has_amber = len(self.amber_segments) > 0
        has_uv = len(self.uv_segments) > 0

        if has_red and has_green and has_blue:
            found_color += ColorSupport.HAS_RGB_SUPPORT
        if has_uv:
            found_color += ColorSupport.HAS_UV_SEGMENT
        if has_amber:
            found_color += ColorSupport.HAS_AMBER_SEGMENT
        if has_white:
            found_color += ColorSupport.HAS_WHITE_SEGMENT
        return found_color

    @property
    def first_channel(self) -> int:
        i = 513
        for c in self.channels:
            if c.address < i:
                i = c.address
        if i == 513:
            i = -1
        return i


def make_used_fixture(fixture: Fixture, mode_index: int, universe_id: int) -> UsedFixture:
    """generate a new Used Fixture from a fixture"""
    return UsedFixture(fixture['name'], fixture['shortName'], fixture['categories'], fixture['comment'],
                       fixture['modes'][mode_index], fixture["fileName"], mode_index, universe_id)
