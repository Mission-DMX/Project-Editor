"""Launch helper for the preset editor dialog.

Used by the property pane's "Edit preset..." / "New preset..." menu entries.
The pane itself is still being built (WP11), so this helper is already
available so WP11 can wire it in without further changes here.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from model.virtual_filters.property_cues.presets import EffectPreset, load_preset_library
from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
    PresetEditorDialog,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def open_preset_editor(
    parent: QWidget | None,
    existing_name: str | None,
    user_dir: Path | None = None,
) -> EffectPreset | None:
    """Open the preset editor dialog, optionally pre-populated by name.

    Returns the authored :class:`EffectPreset` on save, or ``None`` on cancel.
    """
    existing: EffectPreset | None = None
    if existing_name:
        library = load_preset_library(user_dir=str(user_dir) if user_dir is not None else None)
        existing = library.get(existing_name)
    dialog = PresetEditorDialog(existing=existing, user_dir=user_dir, parent=parent)
    if dialog.exec():
        return dialog.result_preset()
    return None
