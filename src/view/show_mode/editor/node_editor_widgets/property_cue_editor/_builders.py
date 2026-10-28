"""UI assembly helpers for the property-cue editor shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QVBoxLayout,
)

from view.show_mode.editor.node_editor_widgets.property_cue_editor._settings_panel import build_settings_panel
from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import PropertyPane
from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import StepFixtureTree

if TYPE_CHECKING:
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import PropertyCueEditor


def build_root_ui(editor: PropertyCueEditor) -> None:
    layout = QVBoxLayout()
    editor._root.setLayout(layout)

    editor._cue_table = QTableWidget(0, 3)
    editor._cue_table.setHorizontalHeaderLabels(["#", "Name", "Steps"])
    editor._cue_table.verticalHeader().setVisible(False)
    editor._cue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    editor._cue_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    editor._cue_table.itemSelectionChanged.connect(editor._cue_selection_changed)
    layout.addWidget(editor._cue_table)

    cue_button_row = QHBoxLayout()
    editor._add_cue_button = QPushButton("Add cue")
    editor._add_cue_button.clicked.connect(editor._add_cue)
    cue_button_row.addWidget(editor._add_cue_button)
    editor._add_step_button = QPushButton("Add step")
    editor._add_step_button.clicked.connect(editor._add_step)
    editor._add_step_button.setEnabled(False)
    cue_button_row.addWidget(editor._add_step_button)
    cue_button_row.addStretch(1)
    layout.addLayout(cue_button_row)

    layout.addWidget(build_settings_panel(editor))

    button_row = QHBoxLayout()
    editor._configure_button = QPushButton("Configure fixtures...")
    editor._configure_button.clicked.connect(editor._launch_wizard)
    button_row.addWidget(editor._configure_button)
    editor._preview_button = QPushButton("Start preview")
    editor._preview_button.clicked.connect(editor._toggle_preview)
    editor._preview_button.setEnabled(editor._preview_controller is not None)
    button_row.addWidget(editor._preview_button)
    button_row.addStretch(1)
    layout.addLayout(button_row)

    editor._splitter = QSplitter(Qt.Orientation.Vertical)
    editor._step_tree_placeholder = QLabel("Select a cue to show its steps.")
    editor._property_pane_placeholder = QLabel("Select a property in the tree to edit it.")
    editor._step_tree_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
    editor._property_pane_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
    editor._splitter.addWidget(editor._step_tree_placeholder)
    editor._splitter.addWidget(editor._property_pane_placeholder)
    editor._splitter.setStretchFactor(0, 1)
    editor._splitter.setStretchFactor(1, 0)
    layout.addWidget(editor._splitter, 1)
    install_live_panes(editor)
    editor._apply_cue_selection_state()


def install_live_panes(editor: PropertyCueEditor) -> None:
    if editor._property_filter is None or editor._splitter is None:
        return
    model = editor._property_filter.property_model
    editor._step_tree = StepFixtureTree(model, name_resolver=editor._resolve_node_name)
    editor._property_pane = PropertyPane(model, fixture_lookup=editor._lookup_fixtures)
    # The pane's own sizeHint is driven by the placeholder when nothing is
    # selected, so Qt would otherwise shrink the pane below the tallest
    # editor's natural size. Ask the pane what each tab actually needs and
    # cap at a floor of 100 px for environments where sizeHint is 0.
    editor._property_pane.setMinimumHeight(max(100, editor._property_pane.recommended_minimum_height()))
    editor._splitter.replaceWidget(0, editor._step_tree)
    editor._splitter.replaceWidget(1, editor._property_pane)
    editor._splitter.setStretchFactor(0, 2)
    editor._splitter.setStretchFactor(1, 1)
    editor._step_tree.selection_changed.connect(editor._property_pane.show_editor)
    # Apply only redraws the tree summary columns -- cue count/step count are
    # structural and only change through the Add buttons, so we deliberately do
    # NOT refresh the cue table here (that would blow away the user's row
    # selection and reset the tree).
    editor._property_pane.assignment_applied.connect(editor._step_tree.refresh)
    editor._step_tree.set_current_cue(-1)
    editor._property_pane.set_current_cue(-1)
