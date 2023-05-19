from PySide6.QtWidgets import QWidget, QVBoxLayout

from model.ui_configuration import ShowUI
from ._scene_selector_widget import SceneSelectorWidget
from ._ui_area_widget import UIAreaWidget


class ShowUIPlayerWidget(QWidget):
    """This widget contains the complete show mode UI and requires a pointer to the UI layout stored in
    the model in order to be constructed."""
    def __init__(self, ui: ShowUI, parent: QWidget = None):
        """Construct the widget.

        Attributes:
            ui -- The pointer to the show UI structure
            parent -- The Qt parent container owning this player widget
        """
        super().__init__(parent=parent)

        scene_select_and_ui_layout = QVBoxLayout()
        self._scene_name_list = []
        self._scene_selector = SceneSelectorWidget(ui.scenes)
        scene_select_and_ui_layout.addWidget(self._scene_selector)
        self._ui_area = UIAreaWidget(ui)
        scene_select_and_ui_layout.addWidget(self._ui_area)
        self.setLayout(scene_select_and_ui_layout)
