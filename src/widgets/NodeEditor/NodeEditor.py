from PySide6.QtWidgets import QWidget, QTabWidget, QInputDialog

from pyqtgraph.flowchart.NodeLibrary import NodeLibrary

from . import Nodes
from .SceneTabWidget import SceneTabWidget


class NodeEditorWidget(QTabWidget):
    """Node Editor to create and manage filters."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self._library = NodeLibrary()

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

        self.addTab(QWidget(), "+")
        self.addTab(QWidget(), "-")

        self.tabBarClicked.connect(self.tab_bar_clicked)

    def tab_bar_clicked(self, index: int):
        if index == self.tabBar().count() - 2:
            self.add_scene_tab()
        if index == self.tabBar().count() - 1:
            self.remove_scene_tab()

    def add_scene_tab(self) -> None:

        text, ok = QInputDialog.getText(self, "Create a new scene", "Scene name")
        if ok:
            scene_tab = SceneTabWidget(text, self._library.copy())
            self.insertTab(self.tabBar().count() - 2, scene_tab, text)

    def remove_scene_tab(self):
        index, ok = QInputDialog.getInt(self, "Remove a scene", "Scene index (0-index)")
        if ok and 0 <= index < self.tabBar().count() - 2:
            self.tabBar().removeTab(index)
