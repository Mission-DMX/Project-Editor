"""Shell editor widget for the property-based cue vfilter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from model.virtual_filters.property_cues.model.model import EndAction
from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (
    ExternalChannelDefinition,
    PreviewEditWidget,
)
from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import PreviewController
from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import PropertyPane
from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import StepFixtureTree

if TYPE_CHECKING:
    from model import Filter
    from view.show_mode.editor.nodes import FilterNode

logger = getLogger(__name__)


class PropertyCueEditor(PreviewEditWidget):
    """Shell editor; step tree and property pane are filled in by WP11."""

    def __init__(self, f: Filter | None = None) -> None:
        """Initialize the shell editor widget."""
        super().__init__(f)
        self._property_filter: PropertyBasedCueFilter | None = (
            f if isinstance(f, PropertyBasedCueFilter) else None
        )
        if self._property_filter is None:
            logger.error("Property-cue editor received invalid filter: %s", f)
        self._root = QWidget()
        self._cue_table: QTableWidget | None = None
        self._end_action_combo: QComboBox | None = None
        self._restart_on_play_cb: QCheckBox | None = None
        self._persistence_cb: QCheckBox | None = None
        self._default_cue_combo: QComboBox | None = None
        self._configure_button: QPushButton | None = None
        self._preview_button: QPushButton | None = None
        self._splitter: QSplitter | None = None
        self._step_tree_placeholder: QLabel | None = None
        self._property_pane_placeholder: QLabel | None = None
        self._step_tree: StepFixtureTree | None = None
        self._property_pane: PropertyPane | None = None
        self._wizard = None
        self._preview_controller: PreviewController | None = (
            PreviewController(self._property_filter) if self._property_filter is not None else None
        )
        self._preview_active = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        self._root.setLayout(layout)

        self._cue_table = QTableWidget(0, 3)
        self._cue_table.setHorizontalHeaderLabels(["#", "Name", "Steps"])
        self._cue_table.verticalHeader().setVisible(False)
        self._cue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._cue_table)

        layout.addWidget(self._build_settings_panel())

        button_row = QHBoxLayout()
        self._configure_button = QPushButton("Configure fixtures...")
        self._configure_button.clicked.connect(self._launch_wizard)
        button_row.addWidget(self._configure_button)
        self._preview_button = QPushButton("Start preview")
        self._preview_button.clicked.connect(self._toggle_preview)
        self._preview_button.setEnabled(self._preview_controller is not None)
        button_row.addWidget(self._preview_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._step_tree_placeholder = QLabel("Step/fixture tree - populated by WP11")
        self._property_pane_placeholder = QLabel("Property editor - populated by WP11")
        self._step_tree_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._property_pane_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._splitter.addWidget(self._step_tree_placeholder)
        self._splitter.addWidget(self._property_pane_placeholder)
        layout.addWidget(self._splitter, 1)
        self._install_live_panes()

    def _install_live_panes(self) -> None:
        if self._property_filter is None or self._splitter is None:
            return
        model = self._property_filter.property_model
        self._step_tree = StepFixtureTree(model)
        self._property_pane = PropertyPane(model)
        self._splitter.replaceWidget(0, self._step_tree)
        self._splitter.replaceWidget(1, self._property_pane)
        self._step_tree.selection_changed.connect(self._property_pane.show_editor)
        self._property_pane.assignment_applied.connect(self._step_tree.refresh)
        self._step_tree.set_current_cue(0)
        self._property_pane.set_current_cue(0)

    def _build_settings_panel(self) -> QGroupBox:
        settings_group = QGroupBox("General")
        form = QFormLayout()

        self._end_action_combo = QComboBox()
        self._end_action_combo.addItems([a.value for a in EndAction])
        self._end_action_combo.currentTextChanged.connect(self._end_action_changed)
        form.addRow("End action", self._end_action_combo)

        self._restart_on_play_cb = QCheckBox("Restart on play")
        self._restart_on_play_cb.toggled.connect(self._restart_on_play_toggled)
        form.addRow("", self._restart_on_play_cb)

        self._persistence_cb = QCheckBox("Enable persistence")
        self._persistence_cb.toggled.connect(self._persistence_toggled)
        form.addRow("", self._persistence_cb)

        self._default_cue_combo = QComboBox()
        self._default_cue_combo.addItem("No default cue")
        self._default_cue_combo.currentIndexChanged.connect(self._default_cue_changed)
        form.addRow("Default cue", self._default_cue_combo)

        settings_group.setLayout(form)
        return settings_group

    @property
    def step_tree_container(self) -> QWidget:
        return self._step_tree_placeholder

    @property
    def property_pane_container(self) -> QWidget:
        return self._property_pane_placeholder

    def _end_action_changed(self, text: str) -> None:
        if self._property_filter is None:
            return
        try:
            self._property_filter.property_model.general.end_action = EndAction(text)
        except ValueError:
            logger.warning("Unknown end action: %s", text)

    def _restart_on_play_toggled(self, checked: bool) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.restart_on_play = checked

    def _persistence_toggled(self, checked: bool) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.persistence = checked

    def _default_cue_changed(self, index: int) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.default_cue_index = index - 1

    def _launch_wizard(self) -> None:
        if self._property_filter is None:
            logger.error("No filter available; cannot launch wizard.")
            return
        scene = self._property_filter.scene
        board = getattr(scene, "board_configuration", None) if scene is not None else None
        if board is None:
            logger.error("No board configuration available; cannot launch wizard.")
            return
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard import (
            FixtureSelectionWizard,
        )
        self._wizard = FixtureSelectionWizard(
            board,
            initial=self._property_filter.property_model.fixture_selection,
            parent=self._root,
        )
        if self._wizard.exec():
            new_selection = self._wizard.result_selection()
            if new_selection is not None:
                self._property_filter.property_model.fixture_selection = new_selection
                self._refresh_tree()
        self._wizard = None

    def _refresh_tree(self) -> None:
        if self._step_tree is not None:
            self._step_tree.refresh()

    def _refresh_cue_table(self) -> None:
        if self._cue_table is None or self._property_filter is None:
            return
        self._cue_table.setRowCount(0)
        for i, cue in enumerate(self._property_filter.property_model.cues):
            self._cue_table.insertRow(i)
            self._cue_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._cue_table.setItem(i, 1, QTableWidgetItem(cue.name))
            self._cue_table.setItem(i, 2, QTableWidgetItem(str(len(cue.steps))))

    def _refresh_default_cue_combo(self) -> None:
        if self._default_cue_combo is None or self._property_filter is None:
            return
        self._default_cue_combo.blockSignals(True)
        self._default_cue_combo.clear()
        self._default_cue_combo.addItem("No default cue")
        for i, cue in enumerate(self._property_filter.property_model.cues):
            self._default_cue_combo.addItem(f"Cue {i + 1} - {cue.name}")
        idx = self._property_filter.property_model.general.default_cue_index
        self._default_cue_combo.setCurrentIndex(max(0, idx + 1))
        self._default_cue_combo.blockSignals(False)

    def _refresh_settings_from_model(self) -> None:
        if self._property_filter is None:
            return
        general = self._property_filter.property_model.general
        if self._end_action_combo is not None:
            self._end_action_combo.blockSignals(True)
            self._end_action_combo.setCurrentText(general.end_action.value)
            self._end_action_combo.blockSignals(False)
        if self._restart_on_play_cb is not None:
            self._restart_on_play_cb.blockSignals(True)
            self._restart_on_play_cb.setChecked(general.restart_on_play)
            self._restart_on_play_cb.blockSignals(False)
        if self._persistence_cb is not None:
            self._persistence_cb.blockSignals(True)
            self._persistence_cb.setChecked(general.persistence)
            self._persistence_cb.blockSignals(False)

    @override
    def get_channel_list(self) -> list[ExternalChannelDefinition]:
        # Preview mode is wired by WP12; the shell exposes no live preview channels.
        return []

    @override
    def _get_configuration(self) -> dict[str, str]:
        if self._property_filter is None:
            return {}
        self._property_filter.serialize()
        return dict(self._property_filter.filter_configurations)

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        if self._property_filter is None:
            return
        self._property_filter.filter_configurations.update(conf)
        self._property_filter.deserialize()
        self._refresh_cue_table()
        self._refresh_default_cue_combo()
        self._refresh_settings_from_model()

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        return

    @override
    def get_widget(self) -> QWidget:
        return self._root

    @override
    def parent_opened(self) -> None:
        return

    @override
    def parent_closed(self, filter_node: FilterNode) -> None:
        if self._preview_controller is not None:
            self._preview_controller.stop()
            self._preview_active = False
            if self._preview_button is not None:
                self._preview_button.setText("Start preview")
        super().parent_closed(filter_node)

    def _toggle_preview(self) -> None:
        if self._preview_controller is None or self._preview_button is None:
            return
        if self._preview_active:
            self._preview_controller.stop()
            self._preview_active = False
            self._preview_button.setText("Start preview")
            return
        self._preview_controller.set_playing(True)
        self._preview_controller.start()
        self._preview_active = True
        self._preview_button.setText("Stop preview")
