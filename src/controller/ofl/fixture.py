# coding=utf-8
"""Fixture Definitions from OFL """
import json
from enum import Enum, IntFlag
from typing import TypedDict, NotRequired, TYPE_CHECKING

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



def load_fixture(file) -> Fixture:
    """load fixture from OFL json"""
    f = open(file)
    ob: json = json.load(f)
    return Fixture(name=ob["name"], comment=try_load(ob, "comment"), shortName=try_load(ob, "shortName"),
                   categories=ob["categories"], modes=ob["modes"], fileName=file.split("/fixtures/")[1])


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
        self.channels: list["PatchingChannel"] = []
        self.fixture_file: str = fixture_file
        self.mode_index: int = mode_index

    def copy(self):
        """
        This method clones the used fixture entry, except for the occupied channels
        """
        return UsedFixture(self.name, self.short_name, self.categories,
                           self.comment, self.mode, self.fixture_file, self.mode_index, self.parent_universe)

    def check_for_color_property(self) -> ColorSupport:
        found_color = ColorSupport.NO_COLOR_SUPPORT

        has_red = False
        has_green = False
        has_blue = False
        has_white = False
        has_amber = False
        has_uv = False

        for f in self.channels:
            if f.fixture_channel.lower().startswith("red"):
                has_red = True
            if f.fixture_channel.lower().startswith("green"):
                has_green = True
            if f.fixture_channel.lower().startswith("blue"):
                has_blue = True
            if f.fixture_channel.lower().startswith("white"):
                has_white = True
            if f.fixture_channel.lower().startswith("uv"):
                has_uv = True
            if f.fixture_channel.lower().startswith("amber"):
                has_amber = True

        if has_red and has_green and has_blue:
            found_color += ColorSupport.HAS_RGB_SUPPORT
        if has_uv:
            found_color += ColorSupport.HAS_UV_SEGMENT
        if has_amber:
            found_color += ColorSupport.HAS_AMBER_SEGMENT
        if has_white:
            found_color += ColorSupport.HAS_WHITE_SEGMENT
        return found_color


def make_used_fixture(fixture: Fixture, mode_index: int, universe_id: int) -> UsedFixture:
    """generate a new Used Fixture from a fixture"""
    return UsedFixture(fixture['name'], fixture['shortName'], fixture['categories'], fixture['comment'],
                       fixture['modes'][mode_index], fixture["fileName"], mode_index, universe_id)
