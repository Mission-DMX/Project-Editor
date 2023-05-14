import logging

from PySide6.QtGui import QFont

from pyqtgraph.flowchart.Node import Node, Terminal

from DMXModel import Filter
from .NodeGraphicsItems import FilterSettingsItem


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, type: int, name: str, terminals: dict[str, dict[str, str]] = None, allowAddInput=False, allowAddOutput=False, allowRemove=True):
        super().__init__(name, terminals, allowAddInput, allowAddOutput, allowRemove)
        self._filter = Filter(id=name, type=type)

        self.setup_filter()

    def setup_filter(self, filter: Filter = None):
        """Sets the filter. Overrides existing filters.

        FilterNode.filter will be set to filter.
        FilterNode.filter.channel_links will be reset.
        """
        if filter is not None:
            if filter.type != self._filter.type:
                logging.critical(f"Tried to override a filter with a filter of different type")
                return
                # raise ValueError("Filter type wrong")
            self._filter = filter
                
        else:
            for key, _ in self.inputs().items():
                self.filter.channel_links[key] = ""
                
        
        self.fsi = FilterSettingsItem(self._filter, self.graphicsItem())
        font: QFont = self.graphicsItem().nameItem.font()
        font.setPixelSize(12)
        self.graphicsItem().nameItem.setFont(font)
        self.graphicsItem().xChanged.connect(self.update_filter_pos)

        logging.debug(f"Added filter<type={self._filter.type}, id={self._filter.id}>")

    def connected(self, localTerm: Terminal, remoteTerm: Terminal):
        """Handles behaviour if terminal was connected. Adds channel link to filter.
        Could emit signals. See pyqtgraph.flowchart.Node.connected()

        Args:
            localTerm: The terminal on the node itself.
            remoteTerm: The terminal of the other node.
        """
        if localTerm.isInput() and remoteTerm.isOutput():
            self.filter.channel_links[localTerm.name()] = remoteTerm.node().name() + ":" + remoteTerm.name()

    def disconnected(self, localTerm, remoteTerm):
        """Handles behaviour if terminal was disconnected. Removes channel link from filter.
        Could emit signals. See pyqtgraph.flowchart.Node.disconnected()

        Args:
            localTerm: The terminal on the node itself.
            remoteTerm: The terminal of the other node.
        """
        if localTerm.isInput() and remoteTerm.isOutput():
            self.filter.channel_links[localTerm.name()] = ""

    def rename(self, name):
        """Handles behaviour if node was renamed. Changes filter.id.
        Could emit signals. See pyqtgraph.flowchart.Node.rename()

        Args:
            name: The new name of the filter.

        Returns:
            The return value of pyqtgraph.flowchart.Node.rename()
        """
        self.filter.id = name
        return super().rename(name)
    
    def update_filter_pos(self):
        pos = self.graphicsItem().pos()
        self._filter.pos = pos = (pos.x(), pos.y())
    
    @property
    def filter(self) -> Filter:
        """The corrosponding filter"""
        return self._filter


class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = 'Constants8Bit'

    def __init__(self, name):
        super().__init__(type=0, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = "0"


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = 'Constants16Bit'

    def __init__(self, name):
        super().__init__(type=1, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = "0"


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'ConstantsFloat'

    def __init__(self, name):
        super().__init__(type=2, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = "0.0"


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'ConstantsColor'

    def __init__(self, name):
        super().__init__(type=3, name=name, terminals={
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["value"] = "0,0,0"


class Debug8BitNode(FilterNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    nodeName = 'Debug8Bit'

    def __init__(self, name):
        super().__init__(type=4, name=name, terminals={
            'value': {'io': 'in'}
        })


class Debug16BitNode(FilterNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    nodeName = 'Debug16Bit'

    def __init__(self, name):
        super().__init__(type=5, name=name, terminals={
            'value': {'io': 'in'}
        })


class DebugFloatNode(FilterNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    nodeName = 'DebugFloat'

    def __init__(self, name):
        super().__init__(type=6, name=name, terminals={
            'value': {'io': 'in'}
        })


class DebugColorNode(FilterNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    nodeName = 'DebugColor'

    def __init__(self, name):
        super().__init__(type=7, name=name, terminals={
            'value': {'io': 'in'}
        })


class Adapters16To8Bit(FilterNode):
    """Filter to convert a 16 bit value to two 8 bit values."""
    nodeName = 'Adapters16To8Bit'

    def __init__(self, name):
        super().__init__(type=8, name=name, terminals={
            'value': {'io': 'in'},
            'value_lower': {'io': 'out'},
            'value_upper': {'io': 'out'},
        })


class Adapters16ToBool(FilterNode):
    """Filter to convert a 16 bit value to a boolean.
    If input is 0, output is 0, else 1.
    """
    nodeName = 'Adapters16ToBool'

    def __init__(self, name):
        super().__init__(type=9, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArithmeticsMAC(FilterNode):
    """Filter to calculate MAC value.
    value = (factor1 * factor2) + summand
    """
    nodeName = 'ArithmeticsMAC'

    def __init__(self, name):
        super().__init__(type=10, name=name, terminals={
            'factor1': {'io': 'in'},
            'factor2': {'io': 'in'},
            'summand': {'io': 'in'},
            'value': {'io': 'out'}
        })


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = 'Universe'

    universe_ids: list[int] = []

    def __init__(self, name):
        super().__init__(type=11, name=name, terminals={
            f"input_1": {'io': 'in'}
        }, allowAddInput=True)

        self.filter.filter_configurations["universe"] = self.name()[9:]
        self.filter.filter_configurations["input_1"] = "0"

    def addInput(self, name="input", **args):
        """Allows to add up to 512 input channels."""
        next_input = len(self.inputs())
        if next_input >= 512:
            return None
        input = f"input_{next_input + 1}"
        self.filter.filter_configurations[input] = str(next_input)
        return super().addInput(input, **args)
    
    def removeTerminal(self, term):
        if term.isInput():
            name = term.name
            del self.filter.filter_configurations[name[6:]]
        return super().removeTerminal(term)
    
    def setup_filter(self, filter: Filter = None):
        super().setup_filter(filter)
        if filter is not None:
            for _ in range(len(filter.channel_links) - 1):
                self.addInput()


class ArithmeticsFloatTo8Bit(FilterNode):
    """Filter to round a float/double value to an 8 bit value."""
    nodeName = 'ArithmeticsFloatTo8Bit'

    def __init__(self, name):
        super().__init__(type=13, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArithmeticsFloatTo16Bit(FilterNode):
    """Filter to round a float/double value to a 16 bit value."""
    nodeName = 'ArithmeticsFloatTo16Bit'

    def __init__(self, name):
        super().__init__(type=12, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArithmeticsRound(FilterNode):
    """Filter to round a float/double value to a float/double value"""
    nodeName = 'ArithmeticsRound'

    def __init__(self, name):
        super().__init__(type=14, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ColorToRGBNode(FilterNode):
    """Filter to convert a color value to a rgb value."""
    nodeName = 'ColorToRGB'

    def __init__(self, name):
        super().__init__(type=15, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })


class ColorToRGBWNode(FilterNode):
    """Filter to convert a color value to a rgbw value."""
    nodeName = 'ColorToRGBW'

    def __init__(self, name):
        super().__init__(type=16, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'}
        })


class ColorToRGBWANode(FilterNode):
    """Filter to convert a color value to a rgbwa value."""
    nodeName = 'ColorToRGBWA'

    def __init__(self, name):
        super().__init__(type=17, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'},
            'a': {'io': 'out'}
        })


class FloatToColorNode(FilterNode):
    """Filter to convert a float/double value to a color value."""
    nodeName = 'FloatToPixel'

    def __init__(self, name):
        super().__init__(type=18, name=name, terminals={
            'h': {'io': 'in'},
            's': {'io': 'in'},
            'i': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SineNode(FilterNode):
    """Filter to calculate sine value.
    value = factor_outer*sin((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'Sine'

    def __init__(self, name):
        super().__init__(type=19, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })


class CosineNode(FilterNode):
    """Filter to calculate cosine value.
    value = factor_outer*cos((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'Cosine'

    def __init__(self, name):
        super().__init__(type=20, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })


class TangentNode(FilterNode):
    """Filter to calculate tangent value.
    value = factor_outer*tan((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'Tangent'

    def __init__(self, name):
        super().__init__(type=21, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArcsineNode(FilterNode):
    """Filter to calculate arcsine value.
    value = arcsin(value_in)
    """
    nodeName = 'Arcsine'

    def __init__(self, name):
        super().__init__(type=22, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArccosineNode(FilterNode):
    """Filter to calculate arccosine value.
    value = arccos(value_in)
    """
    nodeName = 'Arccosine'

    def __init__(self, name):
        super().__init__(type=23, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ArctangentNode(FilterNode):
    """Filter to calculate arctangent value.
    value = arctan(value_in)
    """
    nodeName = 'Arctangent'

    def __init__(self, name):
        super().__init__(type=24, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SquareWaveNode(FilterNode):
    """Filter to generate a square."""
    nodeName = 'SquareWave'

    def __init__(self, name):
        super().__init__(type=25, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'length': {'io': 'in'},
            'value': {'io': 'out'}
        })


class TriangleWaveNode(FilterNode):
    """Filter to generate a trinagle wave."""
    nodeName = 'TriangelWave'

    def __init__(self, name):
        super().__init__(type=26, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SawtoothWaveNode(FilterNode):
    """Filter to generate a sawtooth wave."""
    nodeName = 'SawtoothWave'

    def __init__(self, name):
        super().__init__(type=27, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })


class LogarithmNode(FilterNode):
    """Filter to calculate a logarithm value.
    value = ln(value_in)
    """
    nodeName = 'Logarithm'

    def __init__(self, name):
        super().__init__(type=28, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class ExponentialNode(FilterNode):
    """Filter to calculate an exponantial value.
    value = exp(value_in)
    """
    nodeName = 'Exponential'

    def __init__(self, name):
        super().__init__(type=29, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })


class MinimumNode(FilterNode):
    """Filter to calculate the minimum of two values.
    value = min(param1, param2)
    """
    nodeName = 'Minimum'

    def __init__(self, name):
        super().__init__(type=30, name=name, terminals={
            'param1': {'io': 'in'},
            'param2': {'io': 'in'},
            'value': {'io': 'out'}
        })


class MaximumNode(FilterNode):
    """Filter to calculate the maximum of two values.
    value = max(param1, param2)
    """
    nodeName = 'Maximum'

    def __init__(self, name):
        super().__init__(type=31, name=name, terminals={
            'param1': {'io': 'in'},
            'param2': {'io': 'in'},
            'value': {'io': 'out'}
        })


class TimeNode(FilterNode):
    """Filter to represent time."""
    nodeName = 'Time'

    def __init__(self, name):
        super().__init__(type=32, name=name, terminals={
            'value': {'io': 'out'}
        })


class SwitchOnDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time on-switch."""
    nodeName = 'SwitchOnDelay8Bit'

    def __init__(self, name):
        super().__init__(type=33, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        
        self.filter.initial_parameters["delay"] = "0.0"
        

class SwitchOnDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time on-switch."""
    nodeName = 'SwitchOnDelay16Bit'

    def __init__(self, name):
        super().__init__(type=34, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        
        self.filter.initial_parameters["delay"] = "0.0"


class SwitchOnDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time on-switch."""
    nodeName = 'SwitchOnDelayFloat'

    def __init__(self, name):
        super().__init__(type=35, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        
        self.filter.initial_parameters["delay"] = "0.0"


class SwitchOffDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time off-switch."""
    nodeName = 'SwitchOffDelay8Bit'

    def __init__(self, name):
        super().__init__(type=36, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["delay"] = "0.0"


class SwitchOffDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time off-switch."""
    nodeName = 'SwitchOffDelay16Bit'

    def __init__(self, name):
        super().__init__(type=37, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        
        self.filter.initial_parameters["delay"] = "0.0"


class SwitchOffDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time off-switch."""
    nodeName = 'SwitchOffDelayFloat'

    def __init__(self, name):
        super().__init__(type=38, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        
        self.filter.initial_parameters["delay"] = "0.0"
