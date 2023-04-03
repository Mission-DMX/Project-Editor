"""GUI and control elements for the software."""

import sys
import logging


from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt

from DMXModel import Universe
from Network import NetworkManager
from src.Style import Style
from src.widgets.CustomEditor.CustomEditor import CustomEditorWidget
from src.widgets.DirectEditor.DirectEditorWidget import DirectEditorWidget


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget."""

    def __init__(self, parent=None):
        """Inits the MainWindow.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Project-Editor")

        # DMX data. Each universe contains 512 channels
        self._universes: list[Universe] = [Universe(universe_id) for universe_id in range(1, 5)]

        self._fisch_connector: NetworkManager = NetworkManager()
        self._fisch_connector.start()

        for universe in self._universes:
            self._fisch_connector.generate_universe(universe)

        splitter = QtWidgets.QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        self.setCentralWidget(splitter)

        self._custom_editor: CustomEditorWidget = CustomEditorWidget(self._universes, parent=self.centralWidget())
        splitter.addWidget(self._custom_editor)

        # QWidget to edit channels directly.
        self._direct_editor: DirectEditorWidget = DirectEditorWidget(self._universes, self._fisch_connector,
                                                                     parent=self.centralWidget())
        splitter.addWidget(self._direct_editor)

        self._setup_menubar()
        self._setup_toolbar()

    def _setup_menubar(self) -> None:
        """Adds a menubar with submenus."""
        self.setMenuBar(QtWidgets.QMenuBar())
        menu_file = QtWidgets.QMenu(self.menuBar())
        menu_file.setTitle("File")
        action_save = QtGui.QAction(self)
        action_save.setText("Save")
        action_save.triggered.connect(self._save_scene)
        self.menuBar().addAction(menu_file.menuAction())
        menu_file.addAction(action_save)

    def _setup_toolbar(self) -> None:
        """Adds a toolbar with actions."""
        toolbar = self.addToolBar("Mode")
        self.__switch_mode_action = QtGui.QAction(self)
        self.__switch_mode_action.setText("Direct Mode")
        self.__switch_mode_action.triggered.connect(self._switch_mode)
        toolbar.addAction(self.__switch_mode_action)

    def _switch_mode(self) -> None:
        """Switches between direct and filter mode."""
        current_mode = self.__switch_mode_action.text()
        if current_mode == "Direct Mode":
            self.__switch_mode_action.setText("Filter Mode")
        else:
            self.__switch_mode_action.setText("Direct Mode")

    def _save_scene(self) -> None:
        """Safes the current scene to a file.
        TODO implement saving to xml file with xsd schema. See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd
        """
        pass


if __name__ == "__main__":
    logging.basicConfig(encoding='utf-8', level=logging.INFO)
    logging.info("start DMXGui")
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    screen_width = app.primaryScreen().size().width()
    screen_height = app.primaryScreen().size().height()
    widget = MainWindow()
    widget.showMaximized()

    sys.exit(app.exec())
