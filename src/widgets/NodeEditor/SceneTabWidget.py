from PySide6.QtWidgets import QWidget, QGridLayout

from pyqtgraph.flowchart.Flowchart import Flowchart
from pyqtgraph.flowchart.library import NodeLibrary

class SceneTabWidget(QWidget):
    def __init__(self, scene_name: str, node_library: NodeLibrary) -> None:
        super().__init__()
        self._name = scene_name
        self._library = node_library
        self._fc = Flowchart(name=self._name)

        self._fc.setLibrary(self._library)
        
        self._fc.removeNode(self._fc.outputNode)
        self._fc.removeNode(self._fc.inputNode)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self._fc.widget().chartWidget)


