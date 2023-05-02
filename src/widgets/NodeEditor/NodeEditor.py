from PySide6.QtWidgets import QWidget, QGridLayout

from pyqtgraph.flowchart import Flowchart, Node
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary


from . import Nodes

class NodeEditorWidget(QWidget):
    """Node Editor to create and manage filters."""
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        
        library = NodeLibrary()
        
        library.addNodeType(Nodes.Constants8BitNode, [('Constants',)])
        library.addNodeType(Nodes.Constants16BitNode, [('Constants',)])
        library.addNodeType(Nodes.ConstantsFloatNode, [('Constants',)])
        library.addNodeType(Nodes.ConstantsColorNode, [('Constants',)])
        
        library.addNodeType(Nodes.Debug8BitNode, [('Debug',)])
        library.addNodeType(Nodes.Debug16BitNode, [('Debug',)])
        library.addNodeType(Nodes.DebugFloatNode, [('Debug',)])
        library.addNodeType(Nodes.DebugColorNode, [('Debug',)])
        
        library.addNodeType(Nodes.Adapters16To8Bit, [('Adapters',)])
        library.addNodeType(Nodes.Adapters16ToBool, [('Adapters',)])
        library.addNodeType(Nodes.UniverseNode, [('Adapters',)])
        library.addNodeType(Nodes.ColorToRGBNode, [('Adapters',)])
        library.addNodeType(Nodes.ColorToRGBWNode, [('Adapters',)])
        library.addNodeType(Nodes.ColorToRGBWANode, [('Adapters',)])
        
        library.addNodeType(Nodes.ArithmeticsMAC, [('Arithmetics',)])
        library.addNodeType(Nodes.ArithmeticsFloatTo8Bit, [('Arithmetics',)])
        library.addNodeType(Nodes.ArithmeticsFloatTo16Bit, [('Arithmetics',)])
        library.addNodeType(Nodes.ArithmeticsRound, [('Arithmetics',)])
        
        fc = Flowchart()
        fc.setLibrary(library)
        
        fc.removeNode(fc.outputNode)
        fc.removeNode(fc.inputNode)
        
        self.setLayout(QGridLayout())
        self.layout().addWidget(fc.widget())