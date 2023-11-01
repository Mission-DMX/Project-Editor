from pyqtgraph.flowchart.Node import NodeGraphicsItem


class FilterNodeGraphicsItem(NodeGraphicsItem):
    """This class provides a custom renderer for filter nodes"""

    def __init__(self, node):
        super().__init__(node)

    def updateTerminals(self):
        super().updateTerminals()
        # TODO draw type hints next to terminal

    def paint(self, p, *args):
        super().paint(p, *args)
        # TODO draw filter type below name
