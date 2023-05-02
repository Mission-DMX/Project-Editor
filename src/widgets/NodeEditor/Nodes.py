from PySide6.QtWidgets import QWidget, QLabel

from pyqtgraph.flowchart.Node import Node, NodeGraphicsItem

from . import Filters
from . import NodeWidgets


class Constants8BitNode(Node):
    nodeName = 'Constants8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })
        self._filter = Filters.Constants8Bit()
        self._widget = NodeWidgets.Constants8BitWidget()

    def process(self, **kargs):
        return {'value': 0}

    def ctrlWidget(self):
        return self._widget


class ConstantsColorNode(Node):
    nodeName = 'ConstantsColor'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })
        self._filter = Filters.ConstantsColor()
        self._widget = NodeWidgets.ConstantsColorWidget()

    def process(self, **kargs):
        return {'value': 1}

    def ctrlWidget(self):
        return self._widget


class ColorToRGBNode(Node):
    nodeName = 'ColorToRGB'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })
        self._filter = Filters.ColorToRGB()
        self._widget = NodeWidgets.ColorToRGBWidget()

    def process(self, value):
        if not value:
            return {'r': 0, 'g': 106, 'b': 163}
        if value == 0:
            return {'r': 0, 'g': 0, 'b': 0}
        if value == 1:
            return {'r': 255, 'g': 255, 'b': 255}

    def ctrlWidget(self):
        return self._widget


class UniverseNode(Node):
    nodeName = 'Universe'

    def __init__(self, name):
        super().__init__(name, terminals={
            f"channel{i}": {'io': 'in'} for i in range(8)
        }, allowAddInput=True)
        self._filter = Filters.Universe()
        self._widget = NodeWidgets.UniverseWidget()

    def process(self, **kargs):
        return {}

    def ctrlWidget(self):
        return self._widget
