from PySide6.QtWidgets import QWidget, QGridLayout

from pyqtgraph.flowchart.Flowchart import Flowchart
from pyqtgraph.flowchart.library import NodeLibrary

from DMXModel import Scene

class SceneTabWidget(QWidget):
    def __init__(self, scene: Scene, node_library: NodeLibrary) -> None:
        super().__init__()
        self._library = node_library
        self._fc = Flowchart(name=scene.human_readable_name)

        self._scene = scene
        self._scene.flowchart = self._fc

        self._fc.setLibrary(self._library)
        
        self._fc.removeNode(self._fc.outputNode)
        self._fc.removeNode(self._fc.inputNode)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self._fc.widget().chartWidget)


