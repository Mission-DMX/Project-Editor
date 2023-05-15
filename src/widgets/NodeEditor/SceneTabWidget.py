import logging

from PySide6.QtWidgets import QWidget, QGridLayout
import PySide6

from pyqtgraph.flowchart.Flowchart import Flowchart, Terminal
from pyqtgraph.flowchart.library import NodeLibrary

from model.board_configuration import Scene, Filter

from . import Nodes

class SceneTabWidget(QWidget):

    _type_to_node: dict[int, type] = {
        0: Nodes.Constants8BitNode.nodeName,
        1: Nodes.Constants16BitNode.nodeName,
        2: Nodes.ConstantsFloatNode.nodeName,
        3: Nodes.ConstantsColorNode.nodeName,
        4: Nodes.Debug8BitNode.nodeName,
        5: Nodes.Debug16BitNode.nodeName,
        6: Nodes.DebugFloatNode.nodeName,
        7: Nodes.DebugColorNode.nodeName,
        8: Nodes.Adapters16To8Bit.nodeName,
        9: Nodes.Adapters16ToBool.nodeName,
        10: Nodes.ArithmeticsMAC.nodeName,
        11: Nodes.UniverseNode.nodeName,
        12: Nodes.ArithmeticsFloatTo16Bit.nodeName,
        13: Nodes.ArithmeticsFloatTo8Bit.nodeName,
        14: Nodes.ArithmeticsRound.nodeName,
        15: Nodes.ColorToRGBNode.nodeName,
        16: Nodes.ColorToRGBWNode.nodeName,
        17: Nodes.ColorToRGBWANode.nodeName,
        18: Nodes.FloatToColorNode.nodeName,
        19: Nodes.SineNode.nodeName,
        20: Nodes.CosineNode.nodeName,
        21: Nodes.TangentNode.nodeName,
        22: Nodes.ArcsineNode.nodeName,
        23: Nodes.ArccosineNode.nodeName,
        24: Nodes.ArctangentNode.nodeName,
        25: Nodes.SquareWaveNode.nodeName,
        26: Nodes.TriangleWaveNode.nodeName,
        27: Nodes.SawtoothWaveNode.nodeName,
        28: Nodes.LogarithmNode.nodeName,
        29: Nodes.ExponentialNode.nodeName,
        30: Nodes.MinimumNode.nodeName,
        31: Nodes.MaximumNode.nodeName,
        32: Nodes.TimeNode.nodeName,
        33: Nodes.SwitchOnDelay8BitNode.nodeName,
        34: Nodes.SwitchOnDelay16BitNode.nodeName,
        35: Nodes.SwitchOnDelayFloatNode.nodeName,
        36: Nodes.SwitchOffDelay8BitNode.nodeName,
        37: Nodes.SwitchOffDelay16BitNode.nodeName,
        38: Nodes.SwitchOffDelayFloatNode.nodeName,
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
                       node.setup_filter(filter)
                       node.graphicsItem().setPos(filter.pos[0], filter.pos[1])
                       logging.debug(f"Added and set up filter {filter.id}")

            elif node.filter not in self._scene.filters:
                node.update_filter_pos()
                self._scene.filters.append(node.filter)


    def addFilter(self, filter: Filter):
        self._scene.flowchart.createNode(self._type_to_node[filter.type], name=filter.id)

    def addFilters(self, filters: list[Filter]):
        self._loading = True
        for filter in filters:
            self.addFilter(filter)
        self._loading = False
        
        for name, node in self._scene.flowchart.nodes().items():
            if not isinstance(node, Nodes.FilterNode):
                logging.warn(f"Trying to connect non-FilterNode {name}")
                continue
            
            for input, output in node.filter.channel_links.items():
                if output == "":
                    continue
                remote_name = output.split(':')[0]
                remote_term = output.split(':')[1]
                remote_node = self._scene.flowchart.nodes()[remote_name]
                if not isinstance(remote_node, Nodes.FilterNode):
                    logging.warn(f"Trying to connect node {name} to non-FilterNode {remote_name}")
                remote_term = remote_node.outputs()[remote_term]
                local_term = node.inputs()[input]
                if not isinstance(remote_term, Terminal) or not isinstance(local_term, Terminal):
                    logging.critical("Fetched non-terminal object while trying to connect terminals")
                    continue
                self._scene.flowchart.connectTerminals(local_term, remote_term)
                
        self._scene.flowchart.arrangeNodes()

    @property
    def scene(self) -> Scene:
        return self._scene

    @property
    def flowchart(self) -> Flowchart:
        return self._scene.flowchart