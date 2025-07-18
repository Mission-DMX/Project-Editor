"""Post-load operations"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model import BoardConfiguration


def link_patched_fixtures(show: BoardConfiguration) -> None:
    # TODO link loaded fixture (group)s to virtual universe output filters
    pass
