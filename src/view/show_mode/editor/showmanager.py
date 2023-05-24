# coding=utf-8
"""Widget to create multiple scenes and manage filters.

Usage (where self is a QWidget and board_configuration is a BoardConfiguration):
    node_editor = NodeEditor(self, board_configuration)
    self.addWidget(node_editor)
"""
from PySide6 import QtGui, QtWidgets
from PySide6.QtWidgets import QWidget, QTabWidget, QTabBar, QInputDialog
from pyqtgraph.flowchart import Flowchart

from file.read import read_document
from file.write import create_xml, write_document
from model.board_configuration import BoardConfiguration, Scene
from .scenetab import SceneTabWidget
from .filter_node_library import FilterNodeLibrary


class ShowManagerWidget(QTabWidget):
    """Node Editor to create and manage filters."""
    def __init__(self, parent: QWidget, board_configuration: BoardConfiguration) -> None:
        super().__init__(parent)

        self._library = FilterNodeLibrary()

        self._board_configuration = board_configuration

        # Buttons to add or remove scenes from show
        self.setTabsClosable(True)
        self.addTab(QWidget(), "+")
        self.tabBar().tabButton(self.count() - 1, QTabBar.ButtonPosition.RightSide).resize(0, 0)

        self.tabBarClicked.connect(self._tab_bar_clicked)
        self.tabCloseRequested.connect(self._delete_scene)

        # Toolbar for io/network actions
        self._toolbar: list[QtGui.QAction] = []
        save_show_file_button = QtGui.QAction("save Scene")
        load_show_file_button = QtGui.QAction("load Scene")
        enter_scene_button = QtGui.QAction("enter Scene")
        send_show_button = QtGui.QAction("send Scene")

        enter_scene_button.triggered.connect(self._enter_scene)
        send_show_button.triggered.connect(self._send_show_file)
        save_show_file_button.triggered.connect(lambda: self._select_file(self._save_show_file))
        load_show_file_button.triggered.connect(lambda: self._select_file(self._load_show_file))

        self._toolbar.append(enter_scene_button)
        self._toolbar.append(send_show_button)
        self._toolbar.append(save_show_file_button)
        self._toolbar.append(load_show_file_button)

        board_configuration.broadcaster.scene_created.connect(self._add_tab)
        board_configuration.broadcaster.delete_scene.connect(self._remove_tab)

    def _select_scene_to_be_removed(self):
        scene_index, ok_button_pressed = QInputDialog.getInt(self, "Remove a scene", "Scene index (0-index)")
        if ok_button_pressed and 0 <= scene_index < self.tabBar().count() - 2:
            self._board_configuration.broadcaster.delete_scene()

    @property
    def toolbar(self) -> list[QtGui.QAction]:
        """toolbar for patching_mode"""
        return self._toolbar

    def _tab_bar_clicked(self, index: int):
        """Handles adding/deleting button action.
        
        Args:
            index: Index of the clicked tab
        """
        # Left to right, first "+" button, second "-" button
        if index == self.tabBar().count() - 1:
            self._add_button_clicked()

    def _add_button_clicked(self):
        scene_name, ok_button_pressed = QInputDialog.getText(self, "Create a new scene", "Scene name")
        if ok_button_pressed:
            flowchart = Flowchart(name=scene_name, library=FilterNodeLibrary())
            scene = Scene(scene_id=len(self._board_configuration.scenes),
                          human_readable_name=scene_name,
                          flowchart=flowchart,
                          board_configuration=self._board_configuration)
            self._board_configuration.broadcaster.scene_created.emit(scene)

    def _add_tab(self, scene: Scene) -> SceneTabWidget | None:
        """Creates a tab for a scene
        
        Args:
            scene: The scene to be added
        """

        # Each scene is represented by its own editor
        scene_tab = SceneTabWidget(scene)
        # Move +/- buttons one to the right and insert new tab for the scene
        self.insertTab(self.tabBar().count() - 1, scene_tab, scene.human_readable_name)
        # When loading scene from a file, set displayed tab to first loaded scene
        if self.count() == 2 or self._board_configuration.default_active_scene == scene.scene_id:
            self.setCurrentWidget(scene_tab)
        return scene_tab

    def _remove_tab(self, scene: Scene):
        """Removes the tab corresponding to the scene.

        Args:
            scene: The that is being deleted.
        """
        for index in range(self.count() - 1):
            tab_widget = self.widget(index)
            if not isinstance(tab_widget, SceneTabWidget):
                # TODO logging.warning()
                continue
            if tab_widget.scene == scene:
                widget_index = self.indexOf(tab_widget)
                if self.count() > 0:
                    self.setCurrentIndex(widget_index - 1)
                self.removeTab(widget_index)
                return

    def _delete_scene(self, index: int):
        """Emits  signal to delete the scene represented by the tab clicked.

        Args:
            index: The index of the tab clicked.
        """
        widget = self.widget(index)
        if not isinstance(widget, SceneTabWidget):
            return
        self._board_configuration.broadcaster.delete_scene.emit(widget.scene)

    def _select_file(self, func) -> None:
        """Opens QFileDialog to select a file.
        
        Args:
            func: Function to be called after file was selected and confirmed. Function gets the file name as a string.
        """
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.fileSelected.connect(func)
        file_dialog.show()

    def _load_show_file(self, file_name: str):
        """Loads a show file.
        
        Args:
            file_name: Path to the file to be loaded
        """
        read_document(file_name, self._board_configuration)

    def _save_show_file(self, file_name: str):
        """Safes the current scene to a file.
        
        Args:
            file_name: Path to the file in which self._board_configuration should be saved.
        """
        xml = create_xml(self._board_configuration)
        write_document(file_name, xml)

    def _enter_scene(self) -> None:
        """Asks for scene id and tells fish to load the scene"""
        # TODO Let network manager listen to broadcaster
        scene_id, ok_button_pressed = QtWidgets.QInputDialog.getInt(self, "Fish: Change scene", "Scene id (0-index)")
        if ok_button_pressed:
            print(f"Switching to scene {scene_id}")
            self._board_configuration.broadcaster.change_active_scene.emit(scene_id)

    def _send_show_file(self) -> None:
        """Send the current board configuration as a xml file to fish"""
        # TODO Let network manager listen to broadcaster
        xml = create_xml(self._board_configuration)
        self._board_configuration.broadcaster.load_show_file(xml)
