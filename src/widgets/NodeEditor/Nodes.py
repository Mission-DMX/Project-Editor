from pyqtgraph.flowchart.Node import Node, Terminal, TextItem

from DMXModel import Filter
from .NodeWidgets import InitialParameterTextItem


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, type: int, name: str, terminals: dict[str, dict[str, str]] = None, allowAddInput=False, allowAddOutput=False, allowRemove=True):
        super().__init__(name, terminals, allowAddInput, allowAddOutput, allowRemove)
        self.filter: Filter = Filter(name, type)

        for key, terminal in self.terminals.items():
            if terminal.isInput():
                self.filter.channel_links[key] = ""
        
        

    def connected(self, localTerm: Terminal, remoteTerm: Terminal):
        if localTerm.isInput() and remoteTerm.isOutput():
            self.filter.channel_links[localTerm.name()] = remoteTerm.node().name() + ":" + remoteTerm.name()

    def disconnected(self, localTerm, remoteTerm):
        if localTerm.isInput() and remoteTerm.isOutput():
            self.filter.channel_links[localTerm.name()] = ""

    def rename(self, name):
        self.filter.id = name
        return super().rename(name)


class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = 'Constants8Bit'

    def __init__(self, name):
        super().__init__(type=0, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = str(0)
        self.ip = InitialParameterTextItem("0", self.graphicsItem(), self.value_changed, self.filter)
        self.ip.moveBy(0, 10)

    def value_changed(self):
        self.filter.initial_parameters["value"] = self.ip.toPlainText()


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = 'Constants16Bit'

    def __init__(self, name):
        super().__init__(type=1, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = str(0)
        self.ip = InitialParameterTextItem("0", self.graphicsItem(), self.value_changed, self.filter)
        self.ip.moveBy(0, 10)

    def value_changed(self):
        self.filter.initial_parameters["value"] = self.ip.toPlainText()


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'ConstantsFloat'

    def __init__(self, name):
        super().__init__(type=2, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = str(0)
        self.ip = InitialParameterTextItem("0.0", self.graphicsItem(), self.value_changed, self.filter)
        self.ip.moveBy(0, 10)

    def value_changed(self):
        self.filter.initial_parameters["value"] = self.ip.toPlainText()


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'ConstantsColor'

    def __init__(self, name):
        super().__init__(type=3, name=name, terminals={
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["value"] = str(0)
        self.ip = InitialParameterTextItem("0.0,0.0,0.0", self.graphicsItem(), self.value_changed, self.filter)
        self.ip.moveBy(0, 10)

    def value_changed(self):
        self.filter.initial_parameters["value"] = self.ip.toPlainText()


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

    def __init__(self, name):
        super().__init__(type=11, name=name, terminals={
            str(i): {'io': 'in'} for i in range(8)
        }, allowAddInput=True)

    def addInput(self, name="Input", **args):
        """Allows to add up to 512 input channels."""
        current_inputs = len(self.terminals)
        if current_inputs >= 512:
            return None
        return super().addInput(str(current_inputs), **args)


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


class SwitchOnDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time on-switch."""
    nodeName = 'SwitchOnDelay16Bit'

    def __init__(self, name):
        super().__init__(type=34, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SwitchOnDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time on-switch."""
    nodeName = 'SwitchOnDelayFloat'

    def __init__(self, name):
        super().__init__(type=35, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SwitchOffDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time off-switch."""
    nodeName = 'SwitchOffDelay8Bit'

    def __init__(self, name):
        super().__init__(type=36, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SwitchOffDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time off-switch."""
    nodeName = 'SwitchOffDelay16Bit'

    def __init__(self, name):
        super().__init__(type=37, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })


class SwitchOffDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time off-switch."""
    nodeName = 'SwitchOffDelayFloat'

    def __init__(self, name):
        super().__init__(type=38, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
