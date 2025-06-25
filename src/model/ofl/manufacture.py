# coding=utf-8
"""manufacturers for fixtures"""
import json
import os.path
from typing import TypedDict, cast, LiteralString

from typing_extensions import NotRequired

from model.ofl.fixture import Fixture, load_fixture


class Manufacture(TypedDict):
    """a Fixture from OFL"""
    name: str
    comment: NotRequired[str]
    website: NotRequired[str]
    rdmID: NotRequired[int]


def generate_manufacturers(fixture_directory: LiteralString) -> list[tuple[Manufacture, list[Fixture]]]:
    """generate all Manufactures"""
    with open(os.path.join(fixture_directory, "manufacturers.json"), "r", encoding='UTF-8') as f:
        ob: dict = json.load(f)
    iter_manufactures = iter(ob)
    next(iter_manufactures)
    manufactures: list[tuple[Manufacture, list[Fixture]]] = []
    for o in iter_manufactures:
        manufacturer_directory = os.path.join(os.path.join(fixture_directory, o))
        fixtures = []
        for filename in os.listdir(manufacturer_directory):
            fixture_file = os.path.join(manufacturer_directory, filename)
            # checking if it is a file
            if os.path.isfile(fixture_file):
                fixtures.append(load_fixture(fixture_file))
        manufactures.append((cast(Manufacture, ob[o]), fixtures))
    return manufactures
