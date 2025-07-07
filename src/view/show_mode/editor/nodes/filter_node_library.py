"""Custom Node Library"""
from pyqtgraph.flowchart.NodeLibrary import NodeLibrary

from view.show_mode.editor.nodes.impl.adapters import (
    Adapter8bitToFloat,
    Adapter8BitToRangeFloat,
    Adapter16BitTo8BitNode,
    Adapter16BitToBoolNode,
    Adapter16bitToFloat,
    Adapter16BitToRangeFloat,
    AdapterColorToFloatsNode,
    AdapterColorToRGBNode,
    AdapterColorToRGBWANode,
    AdapterColorToRGBWNode,
    AdapterFloatTo8BitRange,
    AdapterFloatTo16BitRange,
    AdapterFloatToColorNode,
    AdapterFloatToRange,
    ColorBrightnessMixinNode,
    CombineTwo8BitToSingle16Bit,
    Map8BitTo16Bit,
)
from view.show_mode.editor.nodes.impl.arithmetics import (
    ArithmeticExponentialNode,
    ArithmeticFloatTo8BitNode,
    ArithmeticFloatTo16BitNode,
    ArithmeticLogarithmNode,
    ArithmeticMACNode,
    ArithmeticMaximumNode,
    ArithmeticMinimumNode,
    ArithmeticRoundNode,
    Sum8BitNode,
    Sum16BitNode,
    SumFloatNode,
)
from view.show_mode.editor.nodes.impl.color_manip_nodes import ColorMixerVFilterNode
from view.show_mode.editor.nodes.impl.constants import (
    Constants8BitNode,
    Constants16BitNode,
    ConstantsColorNode,
    ConstantsFloatNode,
    PanTiltConstant,
)
from view.show_mode.editor.nodes.impl.debug import (
    Debug8BitNode,
    Debug16BitNode,
    DebugColorNode,
    DebugFloatNode,
    DebugRemote8BitNode,
    DebugRemote16BitNode,
    DebugRemoteColorNode,
    DebugRemoteFloatNode,
)
from view.show_mode.editor.nodes.impl.effects import (
    AutoTrackerNode,
    CueListNode,
    EffectsStackNode,
    Shift8BitNode,
    Shift16BitNode,
    ShiftColorNode,
    ShiftFloatNode,
)
from view.show_mode.editor.nodes.impl.faders import (
    FaderHSIANode,
    FaderHSIAUNode,
    FaderHSINode,
    FaderHSIUNode,
    FaderMainBrightness,
    FaderRawNode,
)
from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode
from view.show_mode.editor.nodes.impl.time import (
    TimeNode,
    TimeSwitchOffDelay8BitNode,
    TimeSwitchOffDelay16BitNode,
    TimeSwitchOffDelayFloatNode,
    TimeSwitchOnDelay8BitNode,
    TimeSwitchOnDelay16BitNode,
    TimeSwitchOnDelayFloatNode,
)
from view.show_mode.editor.nodes.impl.trigonometics import (
    TrigonometricArcCosNode,
    TrigonometricArcSinNode,
    TrigonometricArcTanNode,
    TrigonometricCosineNode,
    TrigonometricSineNode,
    TrigonometricTangentNode,
)
from view.show_mode.editor.nodes.impl.universenode import UniverseNode
from view.show_mode.editor.nodes.impl.waves import SawtoothWaveNode, SquareWaveNode, TriangleWaveNode
from view.show_mode.editor.nodes.import_node import ImportNode


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
        self._register_color_manip_nodes()
        self._register_time_nodes()
        self._register_fader_nodes()
        self._register_effect_nodes()
        self._register_scripting_nodes()
        self.addNodeType(ImportNode, [("")])

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
        self.addNodeType(Debug8BitNode, [('Debug', 'Fish-Log',)])
        self.addNodeType(Debug16BitNode, [('Debug', 'Fish-Log',)])
        self.addNodeType(DebugFloatNode, [('Debug', 'Fish-Log',)])
        self.addNodeType(DebugColorNode, [('Debug', 'Fish-Log',)])
        self.addNodeType(DebugRemote8BitNode, [('Debug',)])
        self.addNodeType(DebugRemote16BitNode, [('Debug',)])
        self.addNodeType(DebugRemoteFloatNode, [('Debug',)])
        self.addNodeType(DebugRemoteColorNode, [('Debug',)])

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
        self.addNodeType(AdapterFloatToRange, [('Adapters',)])
        self.addNodeType(Adapter16BitToRangeFloat, [('Adapters',)])
        self.addNodeType(Adapter8BitToRangeFloat, [('Adapters',)])
        self.addNodeType(CombineTwo8BitToSingle16Bit, [('Adapters',)])
        self.addNodeType(Map8BitTo16Bit, [('Adapters',)])
        self.addNodeType(ColorBrightnessMixinNode, [('Adapters',)])

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
        self.addNodeType(Sum8BitNode, [('Arithmetics',)])
        self.addNodeType(Sum16BitNode, [('Arithmetics',)])
        self.addNodeType(SumFloatNode, [('Arithmetics',)])

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

    def _register_color_manip_nodes(self):
        self.addNodeType(ColorMixerVFilterNode, [('Color Manip',)])
