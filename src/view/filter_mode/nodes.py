# coding=utf-8
"""Contains all possible filter node types"""
import logging

from PySide6.QtGui import QFont
from pyqtgraph.flowchart.Node import Node, Terminal

from model.board_configuration import Filter, UniverseFilter, DataType
from .node_graphics_item import FilterSettingsItem


class FilterNode(Node):
    """Basic filter node."""

    def __init__(self, filter_type: int, name: str, terminals: dict[str, dict[str, str]] = None, allow_add_input=False):
        super().__init__(name, terminals, allow_add_input)
        self._filter = None
        # Dict with entries (channel, DataType)
        self._in_value_types: dict[str, DataType] = {}
        self._out_value_types: dict[str, DataType] = {}

        # Handle special case of universe filter
        if filter_type == 11:
            self._filter = UniverseFilter(filter_id=name)
        else:
            self._filter = Filter(filter_id=name, filter_type=filter_type)

        self.update_filter_pos()
        self.setup_filter()

    def setup_filter(self, filter_: Filter = None):
        """Sets the filter. Overrides existing filters.

        FilterNode.filter will be set to filter.
        FilterNode.filter.channel_links will be reset.
        """
        # Need to be separate from __init__ to handle creation during loading from file.
        # When loading from file, first the node is created.
        # This triggers a signal inside pyqtgraph which is monitored in SceneTabWidget.
        # When signal is triggered, setup_filter() is called.
        # setup_filter() only gets passed a filter during loading from file.
        # When created through nodeeditor, no filter is passed.
        if filter_ is not None:
            if filter_.filter_type != self._filter.filter_type:
                logging.critical(
                    "Tried to override a filter with a filter of different type (%s vs %s)",
                    filter_.filter_type, self._filter.filter_type)
                return
                # raise ValueError("Filter type wrong")
            self._filter = filter_
        else:
            for key, _ in self.inputs().items():
                self.filter.channel_links[key] = ""

        #if len(self._filter.filter_configurations) > 0 or len(self._filter.initial_parameters) > 0:
        self.fsi = FilterSettingsItem(self._filter, self.graphicsItem())
        font: QFont = self.graphicsItem().nameItem.font()
        font.setPixelSize(12)
        self.graphicsItem().nameItem.setFont(font)
        self.graphicsItem().xChanged.connect(self.update_filter_pos)

        logging.debug("Added filter<type=%s}, id=%s>",
                      self._filter.filter_type, self._filter.filter_id)

    def connected(self, localTerm: Terminal, remoteTerm: Terminal):
        """Handles behaviour if terminal was connected. Adds channel link to filter.
        Could emit signals. See pyqtgraph.flowchart.Node.connected()

        Args:
            localTerm: The terminal on the node itself.
            remoteTerm: The terminal of the other node.
        """
        remote_node = remoteTerm.node()

        if not localTerm.isInput() or not remoteTerm.isOutput():
            return

        if not isinstance(remote_node, FilterNode):
            logging.warning("Tried to non-FilterNode nodes. Forced disconnection.")
            localTerm.disconnectFrom(remoteTerm)
            return

        if not self._in_value_types[localTerm.name()] == remote_node.out_value_types[remoteTerm.name()]:
            logging.warning("Tried to connect incompatible filter channels. Forced disconnection.")
            localTerm.disconnectFrom(remoteTerm)
            return

        self.filter.channel_links[localTerm.name()] = remote_node.name() + ":" + remoteTerm.name()

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
        self.filter.filter_id = name
        return super().rename(name)

    def update_filter_pos(self):
        """Saves nodes position inside the ui to registered filter."""
        pos = self.graphicsItem().pos()
        self._filter.pos = (pos.x(), pos.y())

    @property
    def filter(self) -> Filter:
        """The corresponding filter"""
        return self._filter

    @property
    def in_value_types(self) -> dict[str, DataType]:
        """Dict mapping the names to the data types of the input channels."""
        return self._in_value_types

    @property
    def out_value_types(self) -> dict[str, DataType]:
        """Dict mapping the names to the data types of the output channels."""
        return self._out_value_types


class Constants8BitNode(FilterNode):
    """Filter to represent an 8 bit value."""
    nodeName = 'Constants8Bit'

    def __init__(self, name):
        super().__init__(filter_type=0, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = "0"
        self._out_value_types["value"] = DataType.DT_8_BIT


class Constants16BitNode(FilterNode):
    """Filter to represent a 16 bit value."""
    nodeName = 'Constants16Bit'

    def __init__(self, name):
        super().__init__(filter_type=1, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = "0"
        self._out_value_types["value"] = DataType.DT_16_BIT


class ConstantsFloatNode(FilterNode):
    """Filter to represent a float/double value."""
    nodeName = 'ConstantsFloat'

    def __init__(self, name):
        super().__init__(filter_type=2, name=name, terminals={
            'value': {'io': 'out'}
        })

        self.filter.initial_parameters["value"] = "0.0"
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ConstantsColorNode(FilterNode):
    """Filter to represent a color value.
    TODO specify color format
    """
    nodeName = 'ConstantsColor'

    def __init__(self, name):
        super().__init__(filter_type=3, name=name, terminals={
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["value"] = "0,0,0"
        self._out_value_types["value"] = DataType.DT_COLOR


class Debug8BitNode(FilterNode):
    """Filter to debug an 8 bit value.
    TODO implement visualization
    """
    nodeName = 'Debug8Bit'

    def __init__(self, name):
        super().__init__(filter_type=4, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_8_BIT


class Debug16BitNode(FilterNode):
    """Filter to debug a 16 bit value.
    TODO implement visualization
    """
    nodeName = 'Debug16Bit'

    def __init__(self, name):
        super().__init__(filter_type=5, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_16_BIT


class DebugFloatNode(FilterNode):
    """Filter to debug a float/double value.
    TODO implement visualization
    """
    nodeName = 'DebugFloat'

    def __init__(self, name):
        super().__init__(filter_type=6, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_DOUBLE


class DebugColorNode(FilterNode):
    """Filter to debug a color value.
    TODO implement visualization
    """
    nodeName = 'DebugColor'

    def __init__(self, name):
        super().__init__(filter_type=7, name=name, terminals={
            'value': {'io': 'in'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR


class Adapters16To8Bit(FilterNode):
    """Filter to convert a 16 bit value to two 8 bit values."""
    nodeName = 'Adapters16To8Bit'

    def __init__(self, name):
        super().__init__(filter_type=8, name=name, terminals={
            'value': {'io': 'in'},
            'value_lower': {'io': 'out'},
            'value_upper': {'io': 'out'},
        })
        self._in_value_types["value"] = DataType.DT_16_BIT
        self._out_value_types["value_lower"] = DataType.DT_8_BIT
        self._out_value_types["value_lower"] = DataType.DT_8_BIT


class Adapters16ToBool(FilterNode):
    """Filter to convert a 16 bit value to a boolean.
    If input is 0, output is 0, else 1.
    """
    nodeName = 'Adapters16ToBool'

    def __init__(self, name):
        super().__init__(filter_type=9, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_16_BIT
        self._out_value_types["value"] = DataType.DT_BOOL


class ArithmeticsMAC(FilterNode):
    """Filter to calculate MAC value.
    value = (factor1 * factor2) + summand
    """
    nodeName = 'ArithmeticsMAC'

    def __init__(self, name):
        super().__init__(filter_type=10, name=name, terminals={
            'factor1': {'io': 'in'},
            'factor2': {'io': 'in'},
            'summand': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["factor1"] = DataType.DT_DOUBLE
        self._in_value_types["factor2"] = DataType.DT_DOUBLE
        self._in_value_types["summand"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class UniverseNode(FilterNode):
    """Filter to represent a dmx universe. By default, it has 8 outputs, put more can be added."""
    nodeName = 'Universe'

    universe_ids: list[int] = []

    def __init__(self, name):
        super().__init__(filter_type=11, name=name, terminals={
            "input_1": {'io': 'in'}
        }, allow_add_input=True)

        self.filter.filter_configurations["universe"] = self.name()[9:]
        self.filter.filter_configurations["input_1"] = "0"
        self._in_value_types = {f"input_{i}": DataType.DT_8_BIT for i in range(1, 513)}

    def addInput(self, name="input", **args):
        """Allows to add up to 512 input channels."""
        next_input = len(self.inputs())
        if next_input >= 512:
            return None
        input_channel = f"input_{next_input + 1}"
        self.filter.filter_configurations[input_channel] = str(next_input)
        return super().addInput(input_channel, **args)

    def removeTerminal(self, term):
        if term.isInput():
            del self.filter.filter_configurations[term.name()]
        return super().removeTerminal(term)

    def setup_filter(self, filter_: Filter = None):
        super().setup_filter(filter_)
        if filter_ is not None:
            for _ in range(len(filter_.channel_links) - 1):
                self.addInput()


class ArithmeticsFloatTo16Bit(FilterNode):
    """Filter to round a float/double value to a 16 bit value."""
    nodeName = 'ArithmeticsFloatTo16Bit'

    def __init__(self, name):
        super().__init__(filter_type=12, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_16_BIT


class ArithmeticsFloatTo8Bit(FilterNode):
    """Filter to round a float/double value to an 8 bit value."""
    nodeName = 'ArithmeticsFloatTo8Bit'

    def __init__(self, name):
        super().__init__(filter_type=13, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class ArithmeticsRound(FilterNode):
    """Filter to round a float/double value to a float/double value"""
    nodeName = 'ArithmeticsRound'

    def __init__(self, name):
        super().__init__(filter_type=14, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ColorToRGBNode(FilterNode):
    """Filter to convert a color value to a rgb value."""
    nodeName = 'ColorToRGB'

    def __init__(self, name):
        super().__init__(filter_type=15, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
        self._out_value_types["r"] = DataType.DT_8_BIT
        self._out_value_types["g"] = DataType.DT_8_BIT
        self._out_value_types["b"] = DataType.DT_8_BIT


class ColorToRGBWNode(FilterNode):
    """Filter to convert a color value to a rgbw value."""
    nodeName = 'ColorToRGBW'

    def __init__(self, name):
        super().__init__(filter_type=16, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
        self._out_value_types["r"] = DataType.DT_8_BIT
        self._out_value_types["g"] = DataType.DT_8_BIT
        self._out_value_types["b"] = DataType.DT_8_BIT
        self._out_value_types["w"] = DataType.DT_8_BIT


class ColorToRGBWANode(FilterNode):
    """Filter to convert a color value to a RGBWA value."""
    nodeName = 'ColorToRGBWA'

    def __init__(self, name):
        super().__init__(filter_type=17, name=name, terminals={
            'value': {'io': 'in'},
            'r': {'io': 'out'},
            'g': {'io': 'out'},
            'b': {'io': 'out'},
            'w': {'io': 'out'},
            'a': {'io': 'out'}
        })
        self._in_value_types["value"] = DataType.DT_COLOR
        self._out_value_types["r"] = DataType.DT_8_BIT
        self._out_value_types["g"] = DataType.DT_8_BIT
        self._out_value_types["b"] = DataType.DT_8_BIT
        self._out_value_types["w"] = DataType.DT_8_BIT
        self._out_value_types["a"] = DataType.DT_8_BIT


class FloatToColorNode(FilterNode):
    """Filter to convert a float/double value to a color value."""
    nodeName = 'FloatToPixel'

    def __init__(self, name):
        super().__init__(filter_type=18, name=name, terminals={
            'h': {'io': 'in'},
            's': {'io': 'in'},
            'i': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["h"] = DataType.DT_DOUBLE
        self._in_value_types["s"] = DataType.DT_DOUBLE
        self._in_value_types["i"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_COLOR


class SineNode(FilterNode):
    """Filter to calculate sine value.
    value = factor_outer*sin((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'Sine'

    def __init__(self, name):
        super().__init__(filter_type=19, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class CosineNode(FilterNode):
    """Filter to calculate cosine value.
    value = factor_outer*cos((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'Cosine'

    def __init__(self, name):
        super().__init__(filter_type=20, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class TangentNode(FilterNode):
    """Filter to calculate tangent value.
    value = factor_outer*tan((value_in+phase)*factor_inner) + offset
    """
    nodeName = 'Tangent'

    def __init__(self, name):
        super().__init__(filter_type=21, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArcSinNode(FilterNode):
    """Filter to calculate arcSine value.
    value = arcSin(value_in)
    """
    nodeName = 'ArcSin'

    def __init__(self, name):
        super().__init__(filter_type=22, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArcCosNode(FilterNode):
    """Filter to calculate arcCosine value.
    value = arcCos(value_in)
    """
    nodeName = 'ArcCos'

    def __init__(self, name):
        super().__init__(filter_type=23, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ArcTanNode(FilterNode):
    """Filter to calculate arcTangent value.
    value = arcTan(value_in)
    """
    nodeName = 'ArcTangent'

    def __init__(self, name):
        super().__init__(filter_type=24, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class SquareWaveNode(FilterNode):
    """Filter to generate a square."""
    nodeName = 'SquareWave'

    def __init__(self, name):
        super().__init__(filter_type=25, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'length': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._in_value_types["length"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class TriangleWaveNode(FilterNode):
    """Filter to generate a triangle wave."""
    nodeName = 'TriangleWave'

    def __init__(self, name):
        super().__init__(filter_type=26, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })

        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class SawtoothWaveNode(FilterNode):
    """Filter to generate a sawtooth wave."""
    nodeName = 'SawtoothWave'

    def __init__(self, name):
        super().__init__(filter_type=27, name=name, terminals={
            'value_in': {'io': 'in'},
            'factor_outer': {'io': 'in'},
            'factor_inner': {'io': 'in'},
            'phase': {'io': 'in'},
            'offset': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._in_value_types["factor_outer"] = DataType.DT_DOUBLE
        self._in_value_types["factor_inner"] = DataType.DT_DOUBLE
        self._in_value_types["phase"] = DataType.DT_DOUBLE
        self._in_value_types["offset"] = DataType.DT_DOUBLE
        self._in_value_types["length"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class LogarithmNode(FilterNode):
    """Filter to calculate a logarithm value.
    value = ln(value_in)
    """
    nodeName = 'Logarithm'

    def __init__(self, name):
        super().__init__(filter_type=28, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class ExponentialNode(FilterNode):
    """Filter to calculate an exponential value.
    value = exp(value_in)
    """
    nodeName = 'Exponential'

    def __init__(self, name):
        super().__init__(filter_type=29, name=name, terminals={
            'value_in': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class MinimumNode(FilterNode):
    """Filter to calculate the minimum of two values.
    value = min(param1, param2)
    """
    nodeName = 'Minimum'

    def __init__(self, name):
        super().__init__(filter_type=30, name=name, terminals={
            'param1': {'io': 'in'},
            'param2': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class MaximumNode(FilterNode):
    """Filter to calculate the maximum of two values.
    value = max(param1, param2)
    """
    nodeName = 'Maximum'

    def __init__(self, name):
        super().__init__(filter_type=31, name=name, terminals={
            'param1': {'io': 'in'},
            'param2': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self._in_value_types["value_in"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_DOUBLE


class TimeNode(FilterNode):
    """Filter to represent time."""
    nodeName = 'Time'

    def __init__(self, name):
        super().__init__(filter_type=32, name=name, terminals={
            'value': {'io': 'out'}
        })
        self._out_value_types["value"] = DataType.DT_DOUBLE


class SwitchOnDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time on-switch."""
    nodeName = 'SwitchOnDelay8Bit'

    def __init__(self, name):
        super().__init__(filter_type=33, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class SwitchOnDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time on-switch."""
    nodeName = 'SwitchOnDelay16Bit'

    def __init__(self, name):
        super().__init__(filter_type=34, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class SwitchOnDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time on-switch."""
    nodeName = 'SwitchOnDelayFloat'

    def __init__(self, name):
        super().__init__(filter_type=35, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class SwitchOffDelay8BitNode(FilterNode):
    """Filter to represent an 8 bit - time off-switch."""
    nodeName = 'SwitchOffDelay8Bit'

    def __init__(self, name):
        super().__init__(filter_type=36, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class SwitchOffDelay16BitNode(FilterNode):
    """Filter to represent a 16 bit - time off-switch."""
    nodeName = 'SwitchOffDelay16Bit'

    def __init__(self, name):
        super().__init__(filter_type=37, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


class SwitchOffDelayFloatNode(FilterNode):
    """Filter to represent a float/double - time off-switch."""
    nodeName = 'SwitchOffDelayFloat'

    def __init__(self, name):
        super().__init__(filter_type=38, name=name, terminals={
            'value_in': {'io': 'in'},
            'time': {'io': 'in'},
            'value': {'io': 'out'}
        })
        self.filter.initial_parameters["delay"] = "0.0"

        self._in_value_types["value_in"] = DataType.DT_8_BIT
        self._in_value_types["time"] = DataType.DT_DOUBLE
        self._out_value_types["value"] = DataType.DT_8_BIT


###################################################################################
# Filter to handle hardware inputs
###################################################################################


class FilterFaderColumnRaw(FilterNode):
    """Filter to represent any filter fader"""
    nodeName = "FilterFaderColumnRaw"

    def __init__(self, name):
        super().__init__(filter_type=39, name=name, terminals={
            'fader': {'io': 'out'},
            'encoder': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["fader"] = DataType.DT_16_BIT
        self._out_value_types["encoder"] = DataType.DT_16_BIT


class FilterFaderColumnHSI(FilterNode):
    """Filter to represent a hsi filter fader"""
    nodeName = "FilterFaderColumnHSI"

    def __init__(self, name):
        super().__init__(filter_type=40, name=name, terminals={
            'color': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR


class FilterFaderColumnHSIA(FilterNode):
    """Filter to represent a hsia filter fader"""
    nodeName = "FilterFaderColumnHSIA"

    def __init__(self, name):
        super().__init__(filter_type=41, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR
        self._out_value_types["amber"] = DataType.DT_8_BIT


class FilterFaderColumnHSIU(FilterNode):
    """Filter to represent a hsiu filter fader"""
    nodeName = "FilterFaderColumnHSIU"

    def __init__(self, name):
        super().__init__(filter_type=42, name=name, terminals={
            'color': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR
        self._out_value_types["uv"] = DataType.DT_8_BIT


class FilterFaderColumnHSIAU(FilterNode):
    """Filter to represent a hasiau filter fader"""
    nodeName = "FilterFaderColumnHSIAU"

    def __init__(self, name):
        super().__init__(filter_type=43, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        self.filter.filter_configurations["set_id"] = ""
        self.filter.filter_configurations["column_id"] = ""

        self._out_value_types["color"] = DataType.DT_COLOR
        self._out_value_types["amber"] = DataType.DT_8_BIT
        self._out_value_types["uv"] = DataType.DT_8_BIT
