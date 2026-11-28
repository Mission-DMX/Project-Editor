"""UI assembly helpers for the property-cue editor shell."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
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
    # The FilterSettingsDialog sizes itself to its content's ``sizeHint``,
    # so without a minimum the dialog opens too narrow for the cue table and
    # step tree columns to fit without clipping. A 900x720 floor is wide
    # enough to show all property columns ("Dimmer" … "Frost") and tall
    # enough for a couple of visible step rows above the property pane.
    editor._root.setMinimumSize(900, 720)

    editor._cue_table = QTableWidget(0, 3)
    editor._cue_table.setHorizontalHeaderLabels(["#", "Name", "Steps"])
    editor._cue_table.verticalHeader().setVisible(False)
    editor._cue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    editor._cue_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    # Let the Name column take any extra width while the fixed-width ``#``
    # and ``Steps`` columns stay sized to their content.
    cue_header = editor._cue_table.horizontalHeader()
    cue_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    cue_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    cue_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    # Three rows worth of height keeps the cue table compact when there is
    # only one cue but still growable when the user adds more. An empty
    # table reports ``rowHeight(0) == 0`` so we hard-code a reasonable
    # per-row figure here.
    editor._cue_table.setMinimumHeight(editor._cue_table.horizontalHeader().height() + 3 * 28 + 10)
    editor._cue_table.itemSelectionChanged.connect(editor._cue_selection_changed)
    # The Name column is editable in place -- double-click to rename.
    # ``_on_cue_table_item_changed`` writes the new text back into the model.
    editor._cue_table.itemChanged.connect(editor._on_cue_table_item_changed)
    layout.addWidget(editor._cue_table)

    cue_button_row = QHBoxLayout()
    editor._add_cue_button = QPushButton("Add cue")
    editor._add_cue_button.clicked.connect(editor._add_cue)
    cue_button_row.addWidget(editor._add_cue_button)
    editor._add_step_button = QPushButton("Add step")
    editor._add_step_button.clicked.connect(editor._add_step)
    editor._add_step_button.setEnabled(False)
    cue_button_row.addWidget(editor._add_step_button)
    # L19: delete / reorder buttons for both cues and steps.
    editor._delete_cue_button = QPushButton("Delete cue")
    editor._delete_cue_button.clicked.connect(editor._delete_cue)
    editor._delete_cue_button.setEnabled(False)
    cue_button_row.addWidget(editor._delete_cue_button)
    editor._delete_step_button = QPushButton("Delete step")
    editor._delete_step_button.clicked.connect(editor._delete_step)
    editor._delete_step_button.setEnabled(False)
    cue_button_row.addWidget(editor._delete_step_button)
    editor._move_cue_up_button = QPushButton("↑ Cue")
    editor._move_cue_up_button.clicked.connect(lambda: editor._move_cue(-1))
    editor._move_cue_up_button.setEnabled(False)
    cue_button_row.addWidget(editor._move_cue_up_button)
    editor._move_cue_down_button = QPushButton("↓ Cue")
    editor._move_cue_down_button.clicked.connect(lambda: editor._move_cue(1))
    editor._move_cue_down_button.setEnabled(False)
    cue_button_row.addWidget(editor._move_cue_down_button)
    editor._move_step_up_button = QPushButton("↑ Step")
    editor._move_step_up_button.clicked.connect(lambda: editor._move_step(-1))
    editor._move_step_up_button.setEnabled(False)
    cue_button_row.addWidget(editor._move_step_up_button)
    editor._move_step_down_button = QPushButton("↓ Step")
    editor._move_step_down_button.clicked.connect(lambda: editor._move_step(1))
    editor._move_step_down_button.setEnabled(False)
    cue_button_row.addWidget(editor._move_step_down_button)
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
    # On-screen play/pause mirrors the XTouch PLAY button so users without
    # the physical hardware can still drive playback. Disabled until preview
    # is active.
    editor._play_pause_button = QPushButton("Play")
    editor._play_pause_button.clicked.connect(editor._on_play_pause_clicked)
    editor._play_pause_button.setEnabled(False)
    button_row.addWidget(editor._play_pause_button)
    editor._preview_stop_button = QPushButton("Rewind")
    editor._preview_stop_button.clicked.connect(editor._on_preview_rewind_clicked)
    editor._preview_stop_button.setEnabled(False)
    button_row.addWidget(editor._preview_stop_button)
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
    # The property pane carries seven tab editors; forcing the worst-case
    # tab's size as a hard minimum (what we did before) pushed the pane to
    # ~600 px and left the step tree squeezed to its header. A 320 px floor
    # fits the typical editor (dimmer / focus / frost have ~4 rows plus
    # tabs / transition / Apply) and the splitter can still grow it when
    # the dialog is enlarged.
    editor._property_pane.setMinimumHeight(320)
    # Step tree gets its own minimum so it never collapses to the header;
    # two full step rows plus the column header give the user something
    # worth clicking on even in a cramped dialog.
    editor._step_tree.setMinimumHeight(180)
    editor._splitter.replaceWidget(0, editor._step_tree)
    editor._splitter.replaceWidget(1, editor._property_pane)
    editor._splitter.setStretchFactor(0, 2)
    editor._splitter.setStretchFactor(1, 3)
    # Explicitly seed the initial split so Qt doesn't give the whole free
    # area to whichever child reports the taller sizeHint; the stretch
    # factors above govern what happens when the user drags the handle.
    editor._splitter.setSizes([260, 400])
    editor._step_tree.selection_changed.connect(editor._property_pane.show_editor)
    # L11: whenever the step selection changes (mouse or keyboard), update the
    # preview playhead so the XTouch transport operates on the selected step.
    editor._step_tree.selection_changed.connect(editor._on_step_tree_selection_changed)
    # Apply only redraws the tree summary columns -- cue count/step count are
    # structural and only change through the Add buttons, so we deliberately do
    # NOT refresh the cue table here (that would blow away the user's row
    # selection and reset the tree).
    editor._property_pane.assignment_applied.connect(editor._step_tree.refresh)
    # L10: any assignment Apply mutates the model, so drop the vfilter's
    # cached compile before the next preview rebuild uses stale data.
    editor._property_pane.assignment_applied.connect(editor._invalidate_cache)
    editor._step_tree.set_current_cue(-1)
    editor._property_pane.set_current_cue(-1)
