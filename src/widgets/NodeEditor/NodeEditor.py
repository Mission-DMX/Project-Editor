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
        library.addNodeType(Nodes.ConstantsColorNode, [('Constants',)])
        library.addNodeType(Nodes.ColorToRGBNode, [('Adapters',)])
        library.addNodeType(Nodes.UniverseNode, [('Adapters',)])
        
        
        fc = Flowchart()
        fc.setLibrary(library)
        
        fc.removeNode(fc.outputNode)
        fc.removeNode(fc.inputNode)
        
        self.setLayout(QGridLayout())
        self.layout().addWidget(fc.widget())