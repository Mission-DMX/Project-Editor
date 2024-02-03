"""Module containing and exporting all available filter nodes"""
from view.show_mode.editor.nodes.impl.constants import *
from view.show_mode.editor.nodes.impl.debug import *
from view.show_mode.editor.nodes.impl.adapters import *
from view.show_mode.editor.nodes.impl.arithmetics import *
from view.show_mode.editor.nodes.impl.trigonometics import *
from view.show_mode.editor.nodes.impl.waves import *
from view.show_mode.editor.nodes.impl.time import *
from view.show_mode.editor.nodes.impl.faders import *
from view.show_mode.editor.nodes.impl.effects import *
from view.show_mode.editor.nodes.impl.universenode import UniverseNode
from view.show_mode.editor.nodes.impl.scripting import *

type_to_node: dict[int, str] = {
        FilterTypeEnumeration.VFILTER_AUTOTRACKER: AutoTrackerNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_8BIT: Constants8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_16_BIT: Constants16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_FLOAT: ConstantsFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_COLOR: ConstantsColorNode.nodeName,
        4: Debug8BitNode.nodeName,
        5: Debug16BitNode.nodeName,
        6: DebugFloatNode.nodeName,
        7: DebugColorNode.nodeName,
        8: Adapter16BitTo8BitNode.nodeName,
        9: Adapter16BitToBoolNode.nodeName,
        10: ArithmeticMACNode.nodeName,
        11: UniverseNode.nodeName,
        12: ArithmeticFloatTo16BitNode.nodeName,
        13: ArithmeticFloatTo8BitNode.nodeName,
        14: ArithmeticRoundNode.nodeName,
        15: AdapterColorToRGBNode.nodeName,
        16: AdapterColorToRGBWNode.nodeName,
        17: AdapterColorToRGBWANode.nodeName,
        18: AdapterFloatToColorNode.nodeName,
        19: TrigonometricSineNode.nodeName,
        20: TrigonometricCosineNode.nodeName,
        21: TrigonometricTangentNode.nodeName,
        22: TrigonometricArcSinNode.nodeName,
        23: TrigonometricArcCosNode.nodeName,
        24: TrigonometricArcTanNode.nodeName,
        25: SquareWaveNode.nodeName,
        26: TriangleWaveNode.nodeName,
        27: SawtoothWaveNode.nodeName,
        28: ArithmeticLogarithmNode.nodeName,
        29: ArithmeticExponentialNode.nodeName,
        30: ArithmeticMinimumNode.nodeName,
        31: ArithmeticMaximumNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT: TimeNode.nodeName,
        33: TimeSwitchOnDelay8BitNode.nodeName,
        34: TimeSwitchOnDelay16BitNode.nodeName,
        35: TimeSwitchOnDelayFloatNode.nodeName,
        36: TimeSwitchOffDelay8BitNode.nodeName,
        37: TimeSwitchOffDelay16BitNode.nodeName,
        38: TimeSwitchOffDelayFloatNode.nodeName,
        39: FaderRawNode.nodeName,
        40: FaderHSINode.nodeName,
        41: FaderHSIANode.nodeName,
        42: FaderHSIUNode.nodeName,
        43: FaderHSIAUNode.nodeName,
        44: CueListNode.nodeName,
        45: Shift8BitNode.nodeName,
        46: Shift16BitNode.nodeName,
        47: ShiftFloatNode.nodeName,
        48: ShiftColorNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS: FaderMainBrightness.nodeName,
        50: LuaFilterNode.nodeName,
        51: Adapter8bitToFloat.nodeName,
        52: Adapter16bitToFloat.nodeName,
        53: AdapterColorToFloatsNode.nodeName,
        54: AdapterFloatTo8BitRange.nodeName,
        55: AdapterFloatTo16BitRange.nodeName,
        56: AdapterFloatToFloatRange.nodeName,
        57: CombineTwo8BitToSingle16Bit.nodeName,
        58: Map8BitTo16Bit.nodeName,
    }
