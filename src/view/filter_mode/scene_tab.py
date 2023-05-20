"""Widget containing a nodeeditor for one scene."""
import logging

from PySide6.QtWidgets import QWidget, QGridLayout

from pyqtgraph.flowchart.Flowchart import Flowchart, Terminal
from pyqtgraph.flowchart.library import NodeLibrary

from model.board_configuration import Scene, Filter, UniverseFilter

from . import nodes

class SceneTabWidget(QWidget):
    """Widget containing a nodeeditor for one scene"""
    # To handle loading from file.
    _type_to_node: dict[int, type] = {
        0: nodes.Constants8BitNode.nodeName,
        1: nodes.Constants16BitNode.nodeName,
        2: nodes.ConstantsFloatNode.nodeName,
        3: nodes.ConstantsColorNode.nodeName,
        4: nodes.Debug8BitNode.nodeName,
        5: nodes.Debug16BitNode.nodeName,
        6: nodes.DebugFloatNode.nodeName,
        7: nodes.DebugColorNode.nodeName,
        8: nodes.Adapters16To8Bit.nodeName,
        9: nodes.Adapters16ToBool.nodeName,
        10: nodes.ArithmeticsMAC.nodeName,
        11: nodes.UniverseNode.nodeName,
        12: nodes.ArithmeticsFloatTo16Bit.nodeName,
        13: nodes.ArithmeticsFloatTo8Bit.nodeName,
        14: nodes.ArithmeticsRound.nodeName,
        15: nodes.ColorToRGBNode.nodeName,
        16: nodes.ColorToRGBWNode.nodeName,
        17: nodes.ColorToRGBWANode.nodeName,
        18: nodes.FloatToColorNode.nodeName,
        19: nodes.SineNode.nodeName,
        20: nodes.CosineNode.nodeName,
        21: nodes.TangentNode.nodeName,
        22: nodes.ArcsineNode.nodeName,
        23: nodes.ArccosineNode.nodeName,
        24: nodes.ArctangentNode.nodeName,
        25: nodes.SquareWaveNode.nodeName,
        26: nodes.TriangleWaveNode.nodeName,
        27: nodes.SawtoothWaveNode.nodeName,
        28: nodes.LogarithmNode.nodeName,
        29: nodes.ExponentialNode.nodeName,
        30: nodes.MinimumNode.nodeName,
        31: nodes.MaximumNode.nodeName,
        32: nodes.TimeNode.nodeName,
        33: nodes.SwitchOnDelay8BitNode.nodeName,
        34: nodes.SwitchOnDelay16BitNode.nodeName,
        35: nodes.SwitchOnDelayFloatNode.nodeName,
        36: nodes.SwitchOffDelay8BitNode.nodeName,
        37: nodes.SwitchOffDelay16BitNode.nodeName,
        38: nodes.SwitchOffDelayFloatNode.nodeName,
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

        self.add_filter(self._scene.filters)

    def _set_filter_on_node(self, _, action, node):
        if not isinstance(node, nodes.FilterNode):
            logging.warning("Tried to add an unknown node: %s", node)
            return
            # raise TypeError("Node type not known")

        if action == 'remove':
            try:
                self._scene.filters.remove(node.filter)
                logging.debug("Removed filter %s", node.filter.filter_id)
            except ValueError:
                logging.warning("Filter of removed node was not registered")

        elif action == 'add':
            if self._loading:
                for filter in self._scene.filters:
                    if filter.filter_id == node.name():
                        node.setup_filter(filter)
                        node.graphicsItem().setPos(filter.pos[0], filter.pos[1])
                        logging.debug("Added and set up filter %s", filter.filter_id)

            elif node.filter not in self._scene.filters:
                node.update_filter_pos()
                self._scene.filters.append(node.filter)
                if isinstance(node.filter, UniverseFilter):
                    node.filter.board_configuration = self._scene.board_configuration


    def add_filter(self, filter: Filter):
        """Add a single filter from outside the nodeeditor.
        
        Args:
            filter: The filter for which a node should be created.
        """
        self._scene.flowchart.createNode(self._type_to_node[filter.filter_type], name=filter.filter_id)

    def add_filters(self, filters: list[Filter]):
        """Handle loading an entire scene.
        
        Args:
            filters: The filters of the scene to be added.
        """
        # Set flag for _set_filter_on_node()
        self._loading = True
        for filter in filters:
            self.add_filter(filter)
        self._loading = False

        # Create connections inside nodeeditor
        for name, node in self._scene.flowchart.nodes().items():
            if not isinstance(node, nodes.FilterNode):
                logging.warning("Trying to connect non-FilterNode %s", name)
                continue

            for input_channel, output_channel in node.filter.channel_links.items():
                if output_channel == "":
                    continue
                remote_name = output_channel.split(':')[0]
                remote_term = output_channel.split(':')[1]
                remote_node = self._scene.flowchart.nodes()[remote_name]
                if not isinstance(remote_node, nodes.FilterNode):
                    logging.warning("Trying to connect node %s to non-FilterNode %s", name, remote_name)
                remote_term = remote_node.outputs()[remote_term]
                local_term = node.inputs()[input_channel]
                if not isinstance(remote_term, Terminal) or not isinstance(local_term, Terminal):
                    logging.critical("Fetched non-terminal object while trying to connect terminals")
                    continue
                self._scene.flowchart.connectTerminals(local_term, remote_term)

    @property
    def scene(self) -> Scene:
        """The scene of the tab"""
        return self._scene

    @property
    def flowchart(self) -> Flowchart:
        """The flowchart of the scene"""
        return self._scene.flowchart
