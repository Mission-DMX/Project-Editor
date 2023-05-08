import json
from enum import Enum
from typing import TypedDict


class Categorie(Enum):
    """"""
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


# class ImportPlugin(TypedDict):
#    plugin: str
#    date: str
#    comment: Optional[str]
class Capabilities:
    dmxRange: tuple[int, int]
    #


class Channel(TypedDict):
    defaultValue: str
    highlightValue: str
    capabilities: list[Capabilities]


class Mode(TypedDict):
    name: str
    shortName: str
    #    rdmPersonalityIndex: int
    #    physical: Physical
    channels: list[Channel]


class Fixture(TypedDict):
    name: str
    shortName: str | None
    categories: set[Categorie]
    #    meta: MetaData
    comment: str
    #    links: Links
    #    helpWanted
    #    rdm
    #    physical
    #    matrix: Matrix
    #    wheels
    #    availableChannels
    #    templateChannels
    modes: list[Mode]


def load_fixture(file) -> Fixture:
    f = open(file)
    ob = json.load(f)
    return Fixture(name=ob["name"],
                   comment=ob["comment"],
                   shortName=try_load(ob,"shortName"),
                   categories=ob["categories"],
                   modes=ob["modes"])

def try_load(ob, name):
    try:
        return ob[name]
    except:
        return ""

