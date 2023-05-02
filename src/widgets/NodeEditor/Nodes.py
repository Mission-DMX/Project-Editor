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


class Constants16BitNode(Node):
    nodeName = 'Constants16Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class ConstantsFloatNode(Node):
    nodeName = 'ConstantsFloat'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class ConstantsColorNode(Node):
    nodeName = 'ConstantsColor'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class Debug8BitNode(Node):
    nodeName = 'Debug8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            '8bit)': {'io': 'in'}
        })


class Debug16BitNode(Node):
    nodeName = 'Debug16Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            '16bit': {'io': 'in'}
        })


class DebugFloatNode(Node):
    nodeName = 'DebugFloat'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'}
        })


class DebugColorNode(Node):
    nodeName = 'DebugColor'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'}
        })


class Adapters16To8Bit(Node):
    nodeName = 'Adapters16To8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            '16bit': {'io': 'in'},
            'value_lower': {'io': 'out'},
            'value_upper': {'io': 'out'},
        })


class Adapters16ToBool(Node):
    nodeName = 'Adapters16ToBool'

    def __init__(self, name):
        super().__init__(name, terminals={
            '16bit': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArithmeticsMAC(Node):
    nodeName = 'ArithmeticsMAC'

    def __init__(self, name):
        super().__init__(name, terminals={
            'factor1': {'io': 'in'},
            'factor2': {'io': 'in'},
            'summand': {'io': 'in'},
            'value': {'io': 'out'}
        })


class UniverseNode(Node):
    nodeName = 'Universe'

    def __init__(self, name):
        super().__init__(name, terminals={
            f"channel{i}": {'io': 'in'} for i in range(8)
        }, allowAddInput=True)
        
        
class ArithmeticsFloatTo8Bit(Node):
    nodeName = 'ArithmeticsFloatTo8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'},
            'value': {'io': 'out'}
        })
          

class ArithmeticsFloatTo16Bit(Node):
    nodeName = 'ArithmeticsFloatTo16Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'},
            'value': {'io': 'out'}
        })
        

class ArithmeticsRound(Node):
    nodeName = 'ArithmeticsRound'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'},
            'value': {'io': 'out'}
        })
        

class ColorToRGBNode(Node):
    nodeName = 'ColorToRGB'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })
        

class ColorToRGBWNode(Node):
    nodeName = 'ColorToRGBW'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'}
        })
        
        
class ColorToRGBWANode(Node):
    nodeName = 'ColorToRGBWA'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'},
            'a': {'io': 'out'}
        })