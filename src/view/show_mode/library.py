# coding=utf-8
"""Custom Node Library"""
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary
from . import nodes

class FilterNodeLibrary(NodeLibrary):
    """Custom Node Library"""
    def __init__(self):
        super().__init__()
        self.reload()

    def reload(self):
        self._register_constants_nodes()
        self._register_debug_nodes()
        self._register_adapters_nodes()
        self._register_arithmetic_nodes()
        self._register_trigonometric_nodes()
        self._register_wave_nodes()
        self._register_time_nodes()
        self._register_fader_nodes()

    def _register_constants_nodes(self):
        """Registers all the constants nodes."""
        # Add Node -> Constants sub menu
        self.addNodeType(nodes.Constants8BitNode, [('Constants',)])
        self.addNodeType(nodes.Constants16BitNode, [('Constants',)])
        self.addNodeType(nodes.ConstantsFloatNode, [('Constants',)])
        self.addNodeType(nodes.ConstantsColorNode, [('Constants',)])

    def _register_debug_nodes(self):
        """Registers all the debugs nodes."""
        # Add Node -> Debug sub menu
        self.addNodeType(nodes.Debug8BitNode, [('Debug',)])
        self.addNodeType(nodes.Debug16BitNode, [('Debug',)])
        self.addNodeType(nodes.DebugFloatNode, [('Debug',)])
        self.addNodeType(nodes.DebugColorNode, [('Debug',)])

    def _register_adapters_nodes(self):
        """Registers all the constants nodes."""
        # Add Node -> Adapters sub menu
        self.addNodeType(nodes.Adapter16BitTo8BitNode, [('Adapters',)])
        self.addNodeType(nodes.Adapter16BitToBoolNode, [('Adapters',)])
        self.addNodeType(nodes.UniverseNode, [('Adapters',)])
        self.addNodeType(nodes.AdapterColorToRGBNode, [('Adapters',)])
        self.addNodeType(nodes.AdapterColorToRGBWNode, [('Adapters',)])
        self.addNodeType(nodes.AdapterColorToRGBWANode, [('Adapters',)])
        self.addNodeType(nodes.AdapterFloatToColorNode, [('Adapters',)])

    def _register_arithmetic_nodes(self):
        """Registers all the arithmetics nodes."""
        # Add Node -> Arithmetic sub menu
        self.addNodeType(nodes.ArithmeticMACNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticFloatTo8BitNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticFloatTo16BitNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticRoundNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticLogarithmNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticExponentialNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticMinimumNode, [('Arithmetics',)])
        self.addNodeType(nodes.ArithmeticMaximumNode, [('Arithmetics',)])

    def _register_trigonometric_nodes(self):
        self.addNodeType(nodes.TrigonometricSineNode, [('Trigonometrics',)])
        self.addNodeType(nodes.TrigonometricCosineNode, [('Trigonometrics',)])
        self.addNodeType(nodes.TrigonometricTangentNode, [('Trigonometrics',)])
        self.addNodeType(nodes.TrigonometricArcSinNode, [('Trigonometrics',)])
        self.addNodeType(nodes.TrigonometricArcCosNode, [('Trigonometrics',)])
        self.addNodeType(nodes.TrigonometricArcTanNode, [('Trigonometrics',)])

    def _register_wave_nodes(self):
        """Registers all the wave nodes."""
        self.addNodeType(nodes.SquareWaveNode, [('Waves',)])
        self.addNodeType(nodes.TriangleWaveNode, [('Waves',)])
        self.addNodeType(nodes.SawtoothWaveNode, [('Waves',)])

    def _register_time_nodes(self):
        """Registers all the time nodes."""
        # Add Node -> Time sub menu
        self.addNodeType(nodes.TimeNode, [('Time',)])
        self.addNodeType(nodes.TimeSwitchOnDelay8BitNode, [('Time',)])
        self.addNodeType(nodes.TimeSwitchOnDelay16BitNode, [('Time',)])
        self.addNodeType(nodes.TimeSwitchOnDelayFloatNode, [('Time',)])
        self.addNodeType(nodes.TimeSwitchOffDelay8BitNode, [('Time',)])
        self.addNodeType(nodes.TimeSwitchOffDelay16BitNode, [('Time',)])
        self.addNodeType(nodes.TimeSwitchOffDelayFloatNode, [('Time',)])

    def _register_fader_nodes(self):
        """Registers all the fader nodes."""
        # Add Node -> Filter Fader sub menu
        self.addNodeType(nodes.FaderRawNode, [('Filter Fader',)])
        self.addNodeType(nodes.FaderHSINode, [('Filter Fader',)])
        self.addNodeType(nodes.FaderHSIANode, [('Filter Fader',)])
        self.addNodeType(nodes.FaderHSIUNode, [('Filter Fader',)])
        self.addNodeType(nodes.FaderHSIAUNode, [('Filter Fader',)])
