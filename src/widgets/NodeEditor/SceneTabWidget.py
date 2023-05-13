import logging

from PySide6.QtWidgets import QWidget, QGridLayout

from pyqtgraph.flowchart.Flowchart import Flowchart
from pyqtgraph.flowchart.library import NodeLibrary

from DMXModel import Scene, Filter

from . import Nodes

class SceneTabWidget(QWidget):

    _type_to_node: dict[int, type] = {
        0: Nodes.Constants8BitNode,
        1: Nodes.Constants16BitNode,
        2: Nodes.ConstantsFloatNode,
        3: Nodes.ConstantsColorNode,
        4: Nodes.Debug8BitNode,
        5: Nodes.Debug16BitNode,
        6: Nodes.DebugFloatNode,
        7: Nodes.DebugColorNode,
        8: Nodes.Adapters16To8Bit,
        9: Nodes.Adapters16ToBool,
        10: Nodes.ArithmeticsMAC,
        11: Nodes.UniverseNode,
        12: Nodes.ArithmeticsFloatTo16Bit,
        13: Nodes.ArithmeticsFloatTo8Bit,
        14: Nodes.ArithmeticsRound,
        15: Nodes.ColorToRGBNode,
        16: Nodes.ColorToRGBWNode,
        17: Nodes.ColorToRGBWANode,
        18: Nodes.FloatToColorNode,
        19: Nodes.SineNode,
        20: Nodes.CosineNode,
        21: Nodes.TangentNode,
        22: Nodes.ArcsineNode,
        23: Nodes.ArccosineNode,
        24: Nodes.ArctangentNode,
        25: Nodes.SquareWaveNode,
        26: Nodes.TriangleWaveNode,
        27: Nodes.SawtoothWaveNode,
        28: Nodes.LogarithmNode,
        29: Nodes.ExponentialNode,
        30: Nodes.MinimumNode,
        31: Nodes.MaximumNode,
        32: Nodes.TimeNode,
        33: Nodes.SwitchOnDelay8BitNode,
        34: Nodes.SwitchOnDelay16BitNode,
        35: Nodes.SwitchOnDelayFloatNode,
        36: Nodes.SwitchOffDelay8BitNode,
        37: Nodes.SwitchOffDelay16BitNode,
        38: Nodes.SwitchOffDelayFloatNode
    }

    def __init__(self, scene: Scene, node_library: NodeLibrary) -> None:
        super().__init__()
        self._library = node_library
        self._scene = scene

        # Flag to differentiate between loading filters from file and creating filters.
        self._loading = False

        self._scene.flowchart.setLibrary(self._library)

        self._scene.flowchart.removeNode(self._scene.flowchart.outputNode)
        self._scene.flowchart.removeNode(self._scene.flowchart.inputNode)
        
        self._scene.flowchart.sigChartChanged.connect(self._set_filter_on_node)

        self.setLayout(QGridLayout())
        self.layout().addWidget(self._scene.flowchart.widget().chartWidget)

        self.addFilters(self._scene.filters)

    def _set_filter_on_node(self, flowchart, action, node):
        if not isinstance(node, Nodes.FilterNode):
                logging.warn(f"Tried to add an unknown node: {node}")
                return
                # raise TypeError("Node type not known")

        if action == 'remove':
            try:
                self._scene.filters.remove(node.filter)
                logging.debug(f"Removed filter {node.filter.id}.")
            except ValueError:
                logging.warn("Filter of removed node was not registered.")

        elif action == 'add':
            if self._loading:
               for filter in self._scene.filters:
                   if filter.id == node.name():
                       node.filter == filter
                       node.setup_filter()
                       logging.debug(f"Added and set up filter {filter.id}")

            elif node.filter not in self._scene.filters:
                self._scene.filters.append(node.filter)


    def addFilter(self, filter: Filter):
        self._scene.flowchart.createNode(self._type_to_node[filter.type], name=filter.id)

    def addFilters(self, filters: list[Filter]):
        self._loading = True
        for filter in filters:
            self.addFilter(filter)
        self._loading = False

    @property
    def scene(self) -> Scene:
        return self._scene

    @property
    def flowchart(self) -> Flowchart:
        return self._scene.flowchart