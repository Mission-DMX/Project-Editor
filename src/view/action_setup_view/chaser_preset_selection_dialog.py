"""Contains dialog to generate commands for a selected chaser preset."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QComboBox, QWidget

from model.filter import FilterTypeEnumeration
from model.filter_data.chaser_model import ChaserModel
from view.action_setup_view._command_insertion_dialog import _CommandInsertionDialog, escape_argument

if TYPE_CHECKING:
    from collections.abc import Callable

    from model import BoardConfiguration
    from model.macro import Macro

class _ChaserPresetSelectionDialog(_CommandInsertionDialog):
    def __init__(self, parent: QWidget, macro: Macro, show: BoardConfiguration, update_callable: Callable) -> None:
        super().__init__(
            parent,
            macro,
            [FilterTypeEnumeration.FILTER_COLOR_CHASER],
            show,
            update_callable,
        )
        self._config_selection_cb = QComboBox()
        self._config_selection_cb.setEditable(False)
        self._config_selection_cb.setEnabled(False)
        self._custom_layout.addWidget(self._config_selection_cb)
        self._custom_layout.setCurrentIndex(0)
        self._chaser_model: ChaserModel | None = None

    @override
    def get_command(self) -> str:
        if self._chaser_model is None:
            return "# Error: Filter model was None!"
        selected_filter = self._filter_selection.selected_filter
        return (
            f"# Switch to chaser preset '{self._config_selection_cb.currentText()}'\n"
            f"extract temp {self._config_selection_cb.currentIndex()} filter-config "
            f'--scene {self._scene.scene_id} {escape_argument(selected_filter.filter_id)} presets "#"\n'
            f"showctl filtermsg {self._scene.scene_id} {escape_argument(self.filter_id)} config $temp"
        )

    @override
    def on_filter_selected(self) -> None:
        self._config_selection_cb.setEnabled(True)
        self._config_selection_cb.clear()
        self._chaser_model = ChaserModel(self._filter_selection.selected_filter.filter_configurations)
        self._config_selection_cb.addItems([preset.name for preset in self._chaser_model.presets])
