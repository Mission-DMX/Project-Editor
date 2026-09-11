"""Post-load operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from controller.utils.network_setting_application import apply_network_settings_and_notify

if TYPE_CHECKING:
    from model import BoardConfiguration


def link_patched_fixtures(show: BoardConfiguration) -> None:
    """Link loaded fixtures and fixture groups to virtual universe output filters."""
    # TODO link loaded fixture (group)s to virtual universe output filters

def apply_show_configurations(show: BoardConfiguration) -> None:
    """Apply the network configuration that ships with the loaded show file."""
    if show.ui_hints.get("network-config-enabled", "false").lower() == "true":
        apply_network_settings_and_notify(show.ui_hints.get("network-config", "{}"))
    else:
        apply_network_settings_and_notify("{}")
