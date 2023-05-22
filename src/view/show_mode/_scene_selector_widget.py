from PySide6 import QtCore
from PySide6.QtWidgets import QScrollArea, QWidget, QHBoxLayout, QPushButton


class SceneSelectorWidget(QScrollArea):
    """This widget allows the switching between the different scenes of the show."""
    def __init__(self, scenes: list[str], parent: QWidget = None):
        """Construct the widget.

        Attributes:
            scenes -- The list of available scene names
        """
        super().__init__(parent=parent)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scene_buttons = []
        self.container = QWidget()
        self._layout = QHBoxLayout()
        for s_name in scenes:
            s_button = QPushButton(s_name)
            self._scene_buttons.append(s_button)
            self._layout.addWidget(s_button)
            # TODO connect button with switch action
        self.container.setLayout(self._layout)
        self.setWidget(self.container)
        self.setWidgetResizable(True)

    # TODO implement switch action
