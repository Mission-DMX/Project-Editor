"""General settings panel builder + refreshers for the property-cue editor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox

from model.virtual_filters.property_cues.model.model import EndAction

if TYPE_CHECKING:
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import PropertyCueEditor


def build_settings_panel(editor: PropertyCueEditor) -> QGroupBox:
    settings_group = QGroupBox("General")
    form = QFormLayout()

    editor._end_action_combo = QComboBox()
    editor._end_action_combo.addItems([a.name for a in EndAction])
    editor._end_action_combo.currentTextChanged.connect(editor._end_action_changed)
    form.addRow("End action", editor._end_action_combo)

    editor._restart_on_play_cb = QCheckBox("Restart on play")
    editor._restart_on_play_cb.toggled.connect(editor._restart_on_play_toggled)
    form.addRow("", editor._restart_on_play_cb)

    editor._persistence_cb = QCheckBox("Enable persistence")
    editor._persistence_cb.toggled.connect(editor._persistence_toggled)
    form.addRow("", editor._persistence_cb)

    editor._default_cue_combo = QComboBox()
    editor._default_cue_combo.addItem("No default cue")
    editor._default_cue_combo.currentIndexChanged.connect(editor._default_cue_changed)
    form.addRow("Default cue", editor._default_cue_combo)

    settings_group.setLayout(form)
    return settings_group


def refresh_default_cue_combo(editor: PropertyCueEditor) -> None:
    if editor._default_cue_combo is None or editor._property_filter is None:
        return
    editor._default_cue_combo.blockSignals(True)
    editor._default_cue_combo.clear()
    editor._default_cue_combo.addItem("No default cue")
    for i, cue in enumerate(editor._property_filter.property_model.cues):
        editor._default_cue_combo.addItem(f"Cue {i + 1} - {cue.name}")
    idx = editor._property_filter.property_model.general.default_cue_index
    editor._default_cue_combo.setCurrentIndex(max(0, idx + 1))
    editor._default_cue_combo.blockSignals(False)


def refresh_settings_from_model(editor: PropertyCueEditor) -> None:
    if editor._property_filter is None:
        return
    general = editor._property_filter.property_model.general
    cue = editor._selected_cue()
    if editor._end_action_combo is not None:
        editor._end_action_combo.blockSignals(True)
        editor._end_action_combo.setCurrentText(cue.end_action.name if cue else EndAction.HOLD.name)
        editor._end_action_combo.blockSignals(False)
    if editor._restart_on_play_cb is not None:
        editor._restart_on_play_cb.blockSignals(True)
        editor._restart_on_play_cb.setChecked(cue.restart_on_play if cue else False)
        editor._restart_on_play_cb.blockSignals(False)
    if editor._persistence_cb is not None:
        editor._persistence_cb.blockSignals(True)
        editor._persistence_cb.setChecked(general.persistence)
        editor._persistence_cb.blockSignals(False)
