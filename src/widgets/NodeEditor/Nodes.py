from pyqtgraph.flowchart.Node import Node

from .Filters import Filter


class FilterNode(Node):
    """Basic filter node."""
    def __init__(self, name, terminals=None, allowAddInput=False, allowAddOutput=False, allowRemove=True):
        super().__init__(name, terminals, allowAddInput, allowAddOutput, allowRemove)
        self._filter_configurations: dict[str, str] = {}
        self._initial_paramters: dict[str, str] = {}

    @property 
    def filter_configuration(self) -> dict[str, str]:
        """The current configuration details."""
        return self._filter_configurations
    
    @property
    def initial_parameters(self) -> dict[str, str]:
        """The initial parameters."""
        return self._initial_paramters
    
    @property
    def channel_link(self) -> dict[str, str]:
        """List of connections for the filter's inputs.
        TODO Implement
        """
        pass 



class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = 'Constants8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = 'Constants16Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'ConstantsFloat'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'ConstantsColor'

    def __init__(self, name):
        super().__init__(name, terminals={
            'value': {'io': 'out'}
        })


class Debug8BitNode(FilterNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    nodeName = 'Debug8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            '8bit)': {'io': 'in'}
        })


class Debug16BitNode(FilterNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    nodeName = 'Debug16Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            '16bit': {'io': 'in'}
        })


class DebugFloatNode(FilterNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    nodeName = 'DebugFloat'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'}
        })


class DebugColorNode(FilterNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    nodeName = 'DebugColor'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'}
        })


class Adapters16To8Bit(FilterNode):
    """Filter to convert a 16 bit value to two 8 bit values."""
    nodeName = 'Adapters16To8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            '16bit': {'io': 'in'},
            'value_lower': {'io': 'out'},
            'value_upper': {'io': 'out'},
        })


class Adapters16ToBool(FilterNode):
    """Filter to convert a 16 bit value to a boolean.
    If input is 0, output is 0, else 1.
    """
    nodeName = 'Adapters16ToBool'

    def __init__(self, name):
        super().__init__(name, terminals={
            '16bit': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArithmeticsMAC(FilterNode):
    """Filter to calculate MAC value.
    value = (factor1 * factor2) + summand
    """
    nodeName = 'ArithmeticsMAC'

    def __init__(self, name):
        super().__init__(name, terminals={
            'factor1': {'io': 'in'},
            'factor2': {'io': 'in'},
            'summand': {'io': 'in'},
            'value': {'io': 'out'}
        })


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = 'Universe'

    def __init__(self, name):
        super().__init__(name, terminals={
            f"channel{i}": {'io': 'in'} for i in range(8)
        }, allowAddInput=True)

    def addInput(self, name="Input", **args):
        """Allows to add up to 512 input channels."""
        current_inputs = len(self.terminals)
        if current_inputs >= 512:
            return None
        return super().addInput(f"channel{current_inputs}", **args)
        
        
class ArithmeticsFloatTo8Bit(FilterNode):
    """Filter to round a float/double value to an 8 bit value."""
    nodeName = 'ArithmeticsFloatTo8Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'},
            'value': {'io': 'out'}
        })
          

class ArithmeticsFloatTo16Bit(FilterNode):
    """Filter to round a float/double value to a 16 bit value."""
    nodeName = 'ArithmeticsFloatTo16Bit'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'},
            'value': {'io': 'out'}
        })
        

class ArithmeticsRound(FilterNode):
    """Filter to round a float/double value to a float/double value"""
    nodeName = 'ArithmeticsRound'

    def __init__(self, name):
        super().__init__(name, terminals={
            'double': {'io': 'in'},
            'value': {'io': 'out'}
        })
        

class ColorToRGBNode(FilterNode):
    """Filter to convert a color value to a rgb value."""
    nodeName = 'ColorToRGB'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })
        

class ColorToRGBWNode(FilterNode):
    """Filter to convert a color value to a rgbw value."""
    nodeName = 'ColorToRGBW'

    def __init__(self, name):
        super().__init__(name, terminals={
            'color': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'}
        })
        
        
class ColorToRGBWANode(FilterNode):
    """Filter to convert a color value to a rgbwa value."""
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