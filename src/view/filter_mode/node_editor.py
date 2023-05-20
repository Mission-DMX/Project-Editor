"""Widget to create multiple scenes and manage filters.

Usage (where self is a QWidget and board_configuration is a BoardConfiguration):
    node_editor = NodeEditor(self, board_configuration)
    self.addWidget(node_editor)
"""
# coding=utf-8
from PySide6 import QtGui, QtWidgets
from PySide6.QtWidgets import QWidget, QTabWidget, QInputDialog
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary
from pyqtgraph.flowchart import Flowchart

from model.board_configuration import BoardConfiguration, Scene
from file.read import read_document
from file.write import create_xml, write_document
from . import nodes
from .scene_tab import SceneTabWidget

class NodeEditorWidget(QTabWidget):
    """Node Editor to create and manage filters."""

    def __init__(self, parent: QWidget, board_configuration: BoardConfiguration) -> None:
        super().__init__(parent)

        self._library = NodeLibrary()

        self._tab_widgets: list[SceneTabWidget] = []

        self._board_configuration = board_configuration

        self._register_constants_nodes()
        self._register_debug_nodes()
        self._register_adapters_nodes()
        self._register_time_nodes()
        self._register_fader_nodes()

        # Buttons to add or remove scenes from show
        self.addTab(QWidget(), "+")
        self.addTab(QWidget(), "-")

        self.tabBarClicked.connect(self._tab_bar_clicked)

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

    def _register_constants_nodes(self):
        """Registers all the constants nodes."""
        # Add Node -> Constants sub menu
        self._library.addNodeType(nodes.Constants8BitNode, [('Constants',)])
        self._library.addNodeType(nodes.Constants16BitNode, [('Constants',)])
        self._library.addNodeType(nodes.ConstantsFloatNode, [('Constants',)])
        self._library.addNodeType(nodes.ConstantsColorNode, [('Constants',)])

    def _register_debug_nodes(self):
        """Registers all the debugs nodes."""
        # Add Node -> Debug sub menu
        self._library.addNodeType(nodes.Debug8BitNode, [('Debug',)])
        self._library.addNodeType(nodes.Debug16BitNode, [('Debug',)])
        self._library.addNodeType(nodes.DebugFloatNode, [('Debug',)])
        self._library.addNodeType(nodes.DebugColorNode, [('Debug',)])

    def _register_adapters_nodes(self):
        """Registers all the constants nodes."""
        # Add Node -> Adapters sub menu
        self._library.addNodeType(nodes.Adapters16To8Bit, [('Adapters',)])
        self._library.addNodeType(nodes.Adapters16ToBool, [('Adapters',)])
        self._library.addNodeType(nodes.UniverseNode, [('Adapters',)])
        self._library.addNodeType(nodes.ColorToRGBNode, [('Adapters',)])
        self._library.addNodeType(nodes.ColorToRGBWNode, [('Adapters',)])
        self._library.addNodeType(nodes.ColorToRGBWANode, [('Adapters',)])
        self._library.addNodeType(nodes.FloatToColorNode, [('Adapters',)])

    def _register_arithmetics_nodes(self):
        """Registers all the arithmetics nodes."""
        # Add Node -> Arithmatics sub menu
        self._library.addNodeType(nodes.ArithmeticsMAC, [('Arithmetics',)])
        self._library.addNodeType(nodes.ArithmeticsFloatTo8Bit, [('Arithmetics',)])
        self._library.addNodeType(nodes.ArithmeticsFloatTo16Bit, [('Arithmetics',)])
        self._library.addNodeType(nodes.ArithmeticsRound, [('Arithmetics',)])
        self._library.addNodeType(nodes.SineNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.CosineNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.TangentNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.ArcsineNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.ArccosineNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.ArctangentNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.SquareWaveNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.TriangleWaveNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.SawtoothWaveNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.LogarithmNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.ExponentialNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.MinimumNode, [('Arithmetics',)])
        self._library.addNodeType(nodes.MaximumNode, [('Arithmetics',)])

    def _register_time_nodes(self):
        """Registers all the time nodes."""
        # Add Node -> Time sub menu
        self._library.addNodeType(nodes.TimeNode, [('Time',)])
        self._library.addNodeType(nodes.SwitchOnDelay8BitNode, [('Time',)])
        self._library.addNodeType(nodes.SwitchOnDelay16BitNode, [('Time',)])
        self._library.addNodeType(nodes.SwitchOnDelayFloatNode, [('Time',)])
        self._library.addNodeType(nodes.SwitchOffDelay8BitNode, [('Time',)])
        self._library.addNodeType(nodes.SwitchOffDelay16BitNode, [('Time',)])
        self._library.addNodeType(nodes.SwitchOffDelayFloatNode, [('Time',)])

    def _register_fader_nodes(self):
        """Registers all the fader nodes."""
        # Add Node -> Filter Fader sub menu
        self._library.addNodeType(nodes.FilterFaderColumnRaw, [('Filter Fader',)])
        self._library.addNodeType(nodes.FilterFaderColumnHSI, [('Filter Fader',)])
        self._library.addNodeType(nodes.FilterFaderColumnHSIA, [('Filter Fader',)])
        self._library.addNodeType(nodes.FilterFaderColumnHSIU, [('Filter Fader',)])
        self._library.addNodeType(nodes.FilterFaderColumnHSIAU, [('Filter Fader',)])

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
        if index == self.tabBar().count() - 2:
            self.add_scene_tab()
        if index == self.tabBar().count() - 1:
            self.remove_scene_tab()

    def add_scene_tab(self, scene: Scene = None) -> SceneTabWidget | None:
        """Creates and adds an nodeeditor. If scene is None, creates a scene, else uses passed scene
        
        Args:
            scene: The scene to be added. If None, create new scene and adds it to self._board_configuration
        """
        # Open dialog to get scene name from user. Aborts if dialog was canceled.
        if scene is None:
            scene_name, ok_button_pressed = QInputDialog.getText(self, "Create a new scene", "Scene name")
            if ok_button_pressed:
                scene = Scene(id=len(self._board_configuration.scenes),
                              human_readable_name=scene_name, flowchart=Flowchart(name=scene_name),
                              board_configuration=self._board_configuration)
                self._board_configuration.scenes.append(scene)
            else:
                return None

        # Each scene is represented by its own editor
        scene_tab = SceneTabWidget(scene, self._library.copy())
        # Move +/- buttons one to the right and insert new tab for the scene
        self.insertTab(self.tabBar().count() - 2, scene_tab, scene.human_readable_name)
        self._tab_widgets.append(scene_tab)
        # When loading scene from a file, set displayed tab to first loaded scene
        # TODO Possibly set to self._board_configuration.default_active_scene
        if len(self._tab_widgets) == 1:
            self.setCurrentWidget(scene_tab)
        return scene_tab

    def remove_scene_tab(self):
        """Creates an dialog, askes for scene id
        and removes it from board configuration and nodeeditor if dialog was confirmed"""
        scene_index, ok_button_pressed = QInputDialog.getInt(self, "Remove a scene", "Scene index (0-index)")
        if ok_button_pressed and 0 <= scene_index < self.tabBar().count() - 2:
            scene = self._tab_widgets[scene_index]
            self._board_configuration.scenes.remove(scene)
            self.tabBar().removeTab(scene_index)

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
        self._board_configuration = read_document(file_name)

        for scene in self._board_configuration.scenes:
            self.add_scene_tab(scene)

    def _save_show_file(self, file_name: str):
        """Safes the current scene to a file.
        
        Args:
            file_name: Path to the file in which self._board_configuration should be saved.
        """
        xml = create_xml(self._board_configuration)
        write_document(file_name, xml)

    def _enter_scene(self) -> None:
        """Asks for scene id and tells fish to load the scene"""
        # TODO Tell fish to load scene using signals
        scene_id, ok_button_pressed = QtWidgets.QInputDialog.getInt(self, "Fish: Change scene", "Scene id (0-index)")
        if ok_button_pressed:
            print(f"Switching to scene {scene_id}")  # self._fish_connector.enter_scene(id)

    def _send_show_file(self) -> None:
        """Send the current board configuration as an xml file to fish"""
        xml = create_xml(self._board_configuration)
        # self._fish_connector.load_show_file(xml=xml, goto_default_scene=True) TODO with signal
