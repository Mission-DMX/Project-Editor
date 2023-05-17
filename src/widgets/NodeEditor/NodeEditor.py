"""Widget to create multiple scenes and manage filters.

Usage (where self is a QWidget and board_configuration is a BoardConfiguration):
    node_editor = NodeEditor(self, board_configuration)
    self.addWidget(node_editor)
"""
from PySide6.QtWidgets import QWidget, QTabWidget, QInputDialog

from pyqtgraph.flowchart.NodeLibrary import NodeLibrary
from pyqtgraph.flowchart import Flowchart

from . import Nodes
from .SceneTabWidget import SceneTabWidget
from model.board_configuration import BoardConfiguration, Scene


class NodeEditorWidget(QTabWidget):
    """Node Editor to create and manage filters."""

    def __init__(self, parent: QWidget, board_configuration: BoardConfiguration) -> None:
        super().__init__(parent)

        self._library = NodeLibrary()

        self._tab_widgets: list[SceneTabWidget] = []

        self._board_configuration = board_configuration

        self._library.addNodeType(Nodes.Constants8BitNode, [('Constants',)])
        self._library.addNodeType(Nodes.Constants16BitNode, [('Constants',)])
        self._library.addNodeType(Nodes.ConstantsFloatNode, [('Constants',)])
        self._library.addNodeType(Nodes.ConstantsColorNode, [('Constants',)])

        self._library.addNodeType(Nodes.Debug8BitNode, [('Debug',)])
        self._library.addNodeType(Nodes.Debug16BitNode, [('Debug',)])
        self._library.addNodeType(Nodes.DebugFloatNode, [('Debug',)])
        self._library.addNodeType(Nodes.DebugColorNode, [('Debug',)])

        self._library.addNodeType(Nodes.Adapters16To8Bit, [('Adapters',)])
        self._library.addNodeType(Nodes.Adapters16ToBool, [('Adapters',)])
        self._library.addNodeType(Nodes.UniverseNode, [('Adapters',)])
        self._library.addNodeType(Nodes.ColorToRGBNode, [('Adapters',)])
        self._library.addNodeType(Nodes.ColorToRGBWNode, [('Adapters',)])
        self._library.addNodeType(Nodes.ColorToRGBWANode, [('Adapters',)])
        self._library.addNodeType(Nodes.FloatToColorNode, [('Adapters',)])
        # self._library.addNodeType(Nodes.<Class Name>,[('Adapters',)])

        self._library.addNodeType(Nodes.ArithmeticsMAC, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ArithmeticsFloatTo8Bit, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ArithmeticsFloatTo16Bit, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ArithmeticsRound, [('Arithmetics',)])
        self._library.addNodeType(Nodes.SineNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.CosineNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.TangentNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ArcsineNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ArccosineNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ArctangentNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.SquareWaveNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.TriangleWaveNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.SawtoothWaveNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.LogarithmNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.ExponentialNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.MinimumNode, [('Arithmetics',)])
        self._library.addNodeType(Nodes.MaximumNode, [('Arithmetics',)])
        # self._library.addNodeType(Nodes.<Class Name>,[('Arithmetics',)])

        self._library.addNodeType(Nodes.TimeNode, [('Time',)])
        self._library.addNodeType(Nodes.SwitchOnDelay8BitNode, [('Time',)])
        self._library.addNodeType(Nodes.SwitchOnDelay16BitNode, [('Time',)])
        self._library.addNodeType(Nodes.SwitchOnDelayFloatNode, [('Time',)])
        self._library.addNodeType(Nodes.SwitchOffDelay8BitNode, [('Time',)])
        self._library.addNodeType(Nodes.SwitchOffDelay16BitNode, [('Time',)])
        self._library.addNodeType(Nodes.SwitchOffDelayFloatNode, [('Time',)])
        
        self._library.addNodeType(Nodes.FilterFaderColumnRaw, [('Filter Fader',)])
        self._library.addNodeType(Nodes.FilterFaderColumnHSI, [('Filter Fader',)])
        self._library.addNodeType(Nodes.FilterFaderColumnHSIA, [('Filter Fader',)])
        self._library.addNodeType(Nodes.FilterFaderColumnHSIU, [('Filter Fader',)])
        self._library.addNodeType(Nodes.FilterFaderColumnHSIAU, [('Filter Fader',)])

        self.addTab(QWidget(), "+")
        self.addTab(QWidget(), "-")

        self.tabBarClicked.connect(self.tab_bar_clicked)

    def tab_bar_clicked(self, index: int):
        if index == self.tabBar().count() - 2:
            self.add_scene_tab()
        if index == self.tabBar().count() - 1:
            self.remove_scene_tab()

    def add_scene_tab(self, scene: Scene = None) -> SceneTabWidget | None:
    
        if scene is None:
            name, ok = QInputDialog.getText(self, "Create a new scene", "Scene name")
            if ok:
                scene = Scene(id=len(self._board_configuration.scenes), human_readable_name=name, flowchart=Flowchart(name=name), board_configuration=self._board_configuration)
                self._board_configuration.scenes.append(scene)
            else:
                return

        scene_tab = SceneTabWidget(scene, self._library.copy())
        self.insertTab(self.tabBar().count() - 2, scene_tab, scene.human_readable_name)
        self._tab_widgets.append(scene_tab)
        if len(self._tab_widgets) == 1:
            self.setCurrentWidget(scene_tab)
        return scene_tab

    def remove_scene_tab(self):
        index, ok = QInputDialog.getInt(self, "Remove a scene", "Scene index (0-index)")
        if ok and 0 <= index < self.tabBar().count() - 2:
            scene = self._tab_widgets[index]
            self._board_configuration.scenes.remove(scene)
            self.tabBar().removeTab(index)
