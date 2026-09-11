"""Post-load operations"""
from __future__ import annotations

from typing import TYPE_CHECKING

from controller.utils.network_setting_application import apply_network_settings_and_notify

if TYPE_CHECKING:
    from model import BoardConfiguration


def link_patched_fixtures(show: BoardConfiguration) -> None:
    # TODO link loaded fixture (group)s to virtual universe output filters
    pass

def apply_show_configurations(show: BoardConfiguration) -> None:
    apply_network_settings_and_notify(show.ui_hints.get("network-config", "{}"))
