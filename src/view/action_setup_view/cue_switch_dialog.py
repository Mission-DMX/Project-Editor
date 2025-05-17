from typing import Callable

from PySide6.QtWidgets import QComboBox, QVBoxLayout, QWidget

from model import BoardConfiguration, Scene
from model.filter import FilterTypeEnumeration
from model.filter_data.cues.cue import Cue
from model.macro import Macro
from view.action_setup_view._command_insertion_dialog import _CommandInsertionDialog


class _InsertCueSwitchDialog(_CommandInsertionDialog):
    def __init__(self, parent: QWidget, macro: Macro, show: BoardConfiguration, update_callable: Callable):
        super().__init__(
            parent, macro,
            [FilterTypeEnumeration.FILTER_TYPE_CUES, FilterTypeEnumeration.VFILTER_CUES],
            show, update_callable
        )

        self._cue_selection_cb = QComboBox(self)
        self._cue_selection_cb.setEditable(False)
        self._cue_selection_cb.setEnabled(False)
        self.custom_layout.addWidget(self._cue_selection_cb)
        self.custom_layout.setCurrentIndex(0)

    def get_command(self) -> str:
        return (f"showctl filtermsg {self._scene.scene_id} {self.filter_id} run_cue "
                f"{self._cue_selection_cb.currentIndex()}  # switch to cue '{self._cue_selection_cb.currentText()}' ")

    def on_filter_selected(self):
        self._cue_selection_cb.setEnabled(True)
        self._cue_selection_cb.clear()
        cue_model: list[Cue] = [
            Cue(s) for s in self._filter_selection.selected_filter.filter_configurations["cuelist"].split("$")
        ]
        self._cue_selection_cb.addItems([c.name for c in cue_model])
