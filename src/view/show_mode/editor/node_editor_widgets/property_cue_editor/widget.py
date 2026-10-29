"""Shell editor widget for the property-based cue vfilter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from model.virtual_filters.property_cues.model.model import EndAction
from model.virtual_filters.property_cues.model.property_cue import PropertyCue
from model.virtual_filters.property_cues.model.property_step import PropertyStep
from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter
from view.show_mode.editor.node_editor_widgets.cue_editor.preview_edit_widget import (
    ExternalChannelDefinition,
    PreviewEditWidget,
)
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.node_editor_widgets.property_cue_editor._board_lookups import (
    lookup_fixtures,
    resolve_node_name,
)
from view.show_mode.editor.node_editor_widgets.property_cue_editor._builders import build_root_ui
from view.show_mode.editor.node_editor_widgets.property_cue_editor._settings_panel import (
    refresh_default_cue_combo,
    refresh_settings_from_model,
)
from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import PreviewController

if TYPE_CHECKING:
    from model import Filter
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.property_pane import PropertyPane
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.step_tree import StepFixtureTree
    from view.show_mode.editor.nodes import FilterNode

logger = getLogger(__name__)


class PropertyCueEditor(PreviewEditWidget):
    """Shell editor; step tree and property pane are filled in by WP11."""

    def __init__(self, f: Filter | None = None) -> None:
        """Initialize the shell editor widget."""
        super().__init__(f)
        self._property_filter: PropertyBasedCueFilter | None = f if isinstance(f, PropertyBasedCueFilter) else None
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
        self._add_cue_button: QPushButton | None = None
        self._add_step_button: QPushButton | None = None
        self._splitter: QSplitter | None = None
        self._step_tree_placeholder: QLabel | None = None
        self._property_pane_placeholder: QLabel | None = None
        self._step_tree: StepFixtureTree | None = None
        self._property_pane: PropertyPane | None = None
        self._wizard = None
        self._preview_prompt: YesNoDialog | None = None
        self._preview_controller: PreviewController | None = (
            PreviewController(self._property_filter) if self._property_filter is not None else None
        )
        self._preview_active = False
        build_root_ui(self)

    @property
    def step_tree_container(self) -> QWidget:
        return self._step_tree_placeholder

    @property
    def property_pane_container(self) -> QWidget:
        return self._property_pane_placeholder

    def _end_action_changed(self, text: str) -> None:
        cue = self._selected_cue()
        if cue is None:
            return
        try:
            cue.end_action = EndAction[text]
        except KeyError:
            logger.warning("Unknown end action: %s", text)

    def _restart_on_play_toggled(self, checked: bool) -> None:
        cue = self._selected_cue()
        if cue is None:
            return
        cue.restart_on_play = checked

    def _selected_cue(self) -> PropertyCue | None:
        if self._property_filter is None or self._cue_table is None:
            return None
        idx = self._cue_table.currentRow()
        cues = self._property_filter.property_model.cues
        if 0 <= idx < len(cues):
            return cues[idx]
        return None

    def _cue_selection_changed(self) -> None:
        self._apply_cue_selection_state()

    def _apply_cue_selection_state(self) -> None:
        cue = self._selected_cue()
        has_cue = cue is not None
        if self._end_action_combo is not None:
            self._end_action_combo.setEnabled(has_cue)
        if self._restart_on_play_cb is not None:
            self._restart_on_play_cb.setEnabled(has_cue)
        if self._add_step_button is not None:
            self._add_step_button.setEnabled(has_cue)
        self._refresh_settings_from_model()
        idx = -1
        if has_cue and self._cue_table is not None:
            idx = self._cue_table.currentRow()
        if self._step_tree is not None:
            self._step_tree.set_current_cue(idx)
        if self._property_pane is not None:
            self._property_pane.set_current_cue(idx)

    def _add_cue(self) -> None:
        if self._property_filter is None or self._cue_table is None:
            return
        model = self._property_filter.property_model
        name = f"Cue {len(model.cues) + 1}"
        new_cue = PropertyCue(name=name, steps=[PropertyStep(name="Step 1")])
        model.cues.append(new_cue)
        self._refresh_cue_table()
        self._refresh_default_cue_combo()
        self._cue_table.selectRow(len(model.cues) - 1)

    def _add_step(self) -> None:
        cue = self._selected_cue()
        if cue is None:
            return
        cue.steps.append(PropertyStep(name=f"Step {len(cue.steps) + 1}"))
        self._refresh_cue_table()
        if self._step_tree is not None:
            self._step_tree.refresh()

    def _persistence_toggled(self, checked: bool) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.persistence = checked

    def _default_cue_changed(self, index: int) -> None:
        if self._property_filter is None:
            return
        self._property_filter.property_model.general.default_cue_index = index - 1

    def _board(self):  # noqa: ANN202 — BoardConfiguration imported lazily
        if self._property_filter is None:
            return None
        scene = self._property_filter.scene
        return getattr(scene, "board_configuration", None) if scene is not None else None

    def _launch_wizard(self) -> None:
        if self._property_filter is None:
            logger.error("No filter available; cannot launch wizard.")
            return
        board = self._board()
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
            self._step_tree.set_name_resolver(self._resolve_node_name)
            self._step_tree.refresh()
        if self._property_pane is not None:
            self._property_pane.refresh_capabilities()

    def _resolve_node_name(self, kind: str, raw_id: str) -> str:
        return resolve_node_name(self._board(), kind, raw_id)

    def _lookup_fixtures(self, node_path: str) -> list:
        model = self._property_filter.property_model if self._property_filter is not None else None
        return lookup_fixtures(self._board(), model, node_path)

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
        refresh_default_cue_combo(self)

    def _refresh_settings_from_model(self) -> None:
        refresh_settings_from_model(self)

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
        if self._cue_table is not None and self._property_filter.property_model.cues:
            self._cue_table.selectRow(0)
        else:
            self._apply_cue_selection_state()

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
        if self._property_filter is not None and not self._property_filter.property_model.fixture_selection.entries:
            self._launch_wizard()
        if self._preview_controller is None:
            return
        self._preview_prompt = YesNoDialog(
            self.get_widget(), "Preview", "Would you like to switch to live preview?",
            self._start_preview,
        )

    @override
    def parent_closed(self, filter_node: FilterNode) -> None:
        self._stop_preview()
        # ``NodeEditorFilterConfigWidget.parent_closed`` (reached via super)
        # calls ``filter_node.update_node_after_settings_changed()``, which in
        # turn triggers :meth:`PropertyBasedCueFilter._rebuild_io` -- that's
        # where the vfilter populates ``out_data_types`` from the current
        # property model so the node grows the configured output terminals.
        super().parent_closed(filter_node)

    def _toggle_preview(self) -> None:
        if self._preview_active:
            self._stop_preview()
        else:
            self._start_preview()

    def _start_preview(self) -> None:
        if self._preview_controller is None or self._preview_button is None or self._preview_active:
            return
        self._preview_controller.set_playing(True)
        self._preview_controller.start()
        self._preview_active = True
        self._preview_button.setText("Stop preview")

    def _stop_preview(self) -> None:
        if self._preview_controller is None:
            return
        self._preview_controller.stop()
        self._preview_active = False
        if self._preview_button is not None:
            self._preview_button.setText("Start preview")
