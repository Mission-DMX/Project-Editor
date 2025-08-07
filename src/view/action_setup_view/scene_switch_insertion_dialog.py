from PySide6.QtWidgets import QComboBox, QDialogButtonBox, QWidget

from model import BoardConfiguration
from model.macro import Macro
from view.action_setup_view._command_insertion_dialog import _CommandInsertionDialog
from view.action_setup_view._command_insertion_dialog import escape_argument as esc


class SceneSwitchInsertionDialog(_CommandInsertionDialog):
    def __init__(self, parent: QWidget, macro: Macro, _show: BoardConfiguration, update_callable: callable) -> None:
        super().__init__(parent, macro, [], _show, update_callable)
        self._scene_selection_cb.setEnabled(False)
        self._scene_selection_cb.setVisible(False)
        self._filter_selection.setEnabled(False)
        self._filter_selection.setVisible(False)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

        self._scene_cb = QComboBox(self)
        for s in self._show.scenes:
            self._scene_cb.addItem(str(s.human_readable_name or s.scene_id), s.scene_id)
        self.custom_layout.addWidget(self._scene_cb)
        self.custom_layout.setCurrentIndex(0)

    def get_command(self) -> str:
        data = self._scene_cb.currentData()
        if data is None:
            return "# please create a scene first."
        return f"showctl select-scene {esc(data)}  # go to scene {self._scene_cb.currentText()}"
