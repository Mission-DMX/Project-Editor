# coding=utf-8
"""Custom Node Library"""
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary

from view.show_mode.editor.nodes.impl.adapters import *
from view.show_mode.editor.nodes.impl.arithmetics import *
from view.show_mode.editor.nodes.impl.constants import *
from view.show_mode.editor.nodes.impl.effects import *
from view.show_mode.editor.nodes.impl.faders import *
from view.show_mode.editor.nodes.impl.scripting import *
from view.show_mode.editor.nodes.impl.trigonometics import *
from view.show_mode.editor.nodes.impl.universenode import *
from view.show_mode.editor.nodes.impl.debug import *
from view.show_mode.editor.nodes.impl.time import *
from view.show_mode.editor.nodes.impl.waves import *


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
        self._register_effect_nodes()
        self._register_scripting_nodes()

    def _register_constants_nodes(self):
        """Registers all the constants nodes."""
        # Add Node -> Constants sub menu
        self.addNodeType(Constants8BitNode, [('Constants',)])
        self.addNodeType(Constants16BitNode, [('Constants',)])
        self.addNodeType(ConstantsFloatNode, [('Constants',)])
        self.addNodeType(ConstantsColorNode, [('Constants',)])
        self.addNodeType(PanTiltConstant, [('Constants',)])

    def _register_debug_nodes(self):
        """Registers all the debugs nodes."""
        # Add Node -> Debug sub menu
        self.addNodeType(Debug8BitNode, [('Debug',)])
        self.addNodeType(Debug16BitNode, [('Debug',)])
        self.addNodeType(DebugFloatNode, [('Debug',)])
        self.addNodeType(DebugColorNode, [('Debug',)])

    def _register_adapters_nodes(self):
        """Registers all the constants nodes."""
        # Add Node -> Adapters sub menu
        self.addNodeType(Adapter16BitTo8BitNode, [('Adapters',)])
        self.addNodeType(Adapter16BitToBoolNode, [('Adapters',)])
        self.addNodeType(UniverseNode, [('Adapters',)])
        self.addNodeType(AdapterColorToRGBNode, [('Adapters',)])
        self.addNodeType(AdapterColorToRGBWNode, [('Adapters',)])
        self.addNodeType(AdapterColorToRGBWANode, [('Adapters',)])
        self.addNodeType(AdapterFloatToColorNode, [('Adapters',)])
        self.addNodeType(AdapterColorToFloatsNode, [('Adapters',)])
        self.addNodeType(Adapter8bitToFloat, [('Adapters',)])
        self.addNodeType(Adapter16bitToFloat, [('Adapters',)])
        self.addNodeType(AdapterFloatTo8BitRange, [('Adapters',)])
        self.addNodeType(AdapterFloatTo16BitRange, [('Adapters',)])
        self.addNodeType(AdapterFloatToFloatRange, [('Adapters',)])
        self.addNodeType(CombineTwo8BitToSingle16Bit, [('Adapters',)])
        self.addNodeType(Map8BitTo16Bit, [('Adapters',)])

    def _register_arithmetic_nodes(self):
        """Registers all the arithmetics nodes."""
        # Add Node -> Arithmetic sub menu
        self.addNodeType(ArithmeticMACNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticFloatTo8BitNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticFloatTo16BitNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticRoundNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticLogarithmNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticExponentialNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticMinimumNode, [('Arithmetics',)])
        self.addNodeType(ArithmeticMaximumNode, [('Arithmetics',)])

    def _register_trigonometric_nodes(self):
        self.addNodeType(TrigonometricSineNode, [('Trigonometrics',)])
        self.addNodeType(TrigonometricCosineNode, [('Trigonometrics',)])
        self.addNodeType(TrigonometricTangentNode, [('Trigonometrics',)])
        self.addNodeType(TrigonometricArcSinNode, [('Trigonometrics',)])
        self.addNodeType(TrigonometricArcCosNode, [('Trigonometrics',)])
        self.addNodeType(TrigonometricArcTanNode, [('Trigonometrics',)])

    def _register_wave_nodes(self):
        """Registers all the wave nodes."""
        self.addNodeType(SquareWaveNode, [('Waves',)])
        self.addNodeType(TriangleWaveNode, [('Waves',)])
        self.addNodeType(SawtoothWaveNode, [('Waves',)])

    def _register_time_nodes(self):
        """Registers all the time nodes."""
        # Add Node -> Time sub menu
        self.addNodeType(TimeNode, [('Time',)])
        self.addNodeType(TimeSwitchOnDelay8BitNode, [('Time',)])
        self.addNodeType(TimeSwitchOnDelay16BitNode, [('Time',)])
        self.addNodeType(TimeSwitchOnDelayFloatNode, [('Time',)])
        self.addNodeType(TimeSwitchOffDelay8BitNode, [('Time',)])
        self.addNodeType(TimeSwitchOffDelay16BitNode, [('Time',)])
        self.addNodeType(TimeSwitchOffDelayFloatNode, [('Time',)])

    def _register_fader_nodes(self):
        """Registers all the fader nodes."""
        # Add Node -> Filter Fader sub menu
        self.addNodeType(FaderMainBrightness, [('Filter Fader',)])
        self.addNodeType(FaderRawNode, [('Filter Fader',)])
        self.addNodeType(FaderHSINode, [('Filter Fader',)])
        self.addNodeType(FaderHSIANode, [('Filter Fader',)])
        self.addNodeType(FaderHSIUNode, [('Filter Fader',)])
        self.addNodeType(FaderHSIAUNode, [('Filter Fader',)])

    def _register_effect_nodes(self):
        self.addNodeType(CueListNode, [('Effects',)])
        self.addNodeType(AutoTrackerNode, [('Effects',)])
        self.addNodeType(Shift8BitNode, [('Effects',)])
        self.addNodeType(Shift16BitNode, [('Effects',)])
        self.addNodeType(ShiftFloatNode, [('Effects',)])
        self.addNodeType(ShiftColorNode, [('Effects',)])
        self.addNodeType(EffectsStackNode, [('Effects',)])

    def _register_scripting_nodes(self):
        self.addNodeType(LuaFilterNode, [('Script',)])
