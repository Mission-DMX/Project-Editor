# coding=utf-8
"""Fixture Definitions from OFL """
import json
from enum import Enum
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
        self.channels: list["PatchingChannel"] = []
        self.fixture_file: str = fixture_file
        self.mode_index: int = mode_index

    def copy(self):
        """
        This method clones the used fixture entry, except for the occupied channels
        """
        return UsedFixture(self.name, self.short_name, self.categories,
                           self.comment, self.mode, self.fixture_file, self.mode_index, self.parent_universe)


def make_used_fixture(fixture: Fixture, mode_index: int, universe_id: int) -> UsedFixture:
    """generate a new Used Fixture from a fixture"""
    return UsedFixture(fixture['name'], fixture['shortName'], fixture['categories'], fixture['comment'],
                       fixture['modes'][mode_index], fixture["fileName"], mode_index, universe_id)
