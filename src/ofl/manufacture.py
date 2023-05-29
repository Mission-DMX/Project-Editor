# coding=utf-8
"""manufacturers for fixtures"""
import json
import os.path
from typing import TypedDict, cast

from typing_extensions import NotRequired

from ofl.fixture import load_fixture, Fixture


class Manufacture(TypedDict):
    """a Fixture from OFL"""
    name: str
    comment: NotRequired[str]
    website: NotRequired[str]
    rdmID: NotRequired[int]


def generate_manufacturers(fixture_directory: os.path) -> list[tuple[Manufacture, list[Fixture]]]:
    """generate all Manufactures"""
    f = open(os.path.join(fixture_directory, 'manufacturers.json'))
    ob: json = json.load(f)
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
