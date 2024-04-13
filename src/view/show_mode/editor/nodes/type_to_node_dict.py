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
        FilterTypeEnumeration.VFILTER_CUES: CueListNode.nodeName,
        FilterTypeEnumeration.VFILTER_AUTOTRACKER: AutoTrackerNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_8BIT: Constants8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_16_BIT: Constants16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_FLOAT: ConstantsFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_CONSTANT_COLOR: ConstantsColorNode.nodeName,
        FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_8BIT: Debug8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_16BIT: Debug16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_FLOAT: DebugFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_COLOR: DebugColorNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT: Adapter16BitTo8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL: Adapter16BitToBoolNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_MAC: ArithmeticMACNode.nodeName,
        FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT: UniverseNode.nodeName,
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
        FilterTypeEnumeration.FILTER_FADER_RAW: FaderRawNode.nodeName,
        FilterTypeEnumeration.FILTER_FADER_HSI: FaderHSINode.nodeName,
        41: FaderHSIANode.nodeName,
        42: FaderHSIUNode.nodeName,
        43: FaderHSIAUNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_CUES: CueListNode.nodeName,
        45: Shift8BitNode.nodeName,
        46: Shift16BitNode.nodeName,
        47: ShiftFloatNode.nodeName,
        48: ShiftColorNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS: FaderMainBrightness.nodeName,
        50: LuaFilterNode.nodeName,
        51: Adapter8bitToFloat.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT: Adapter16bitToFloat.nodeName,
        53: AdapterColorToFloatsNode.nodeName,
        54: AdapterFloatTo8BitRange.nodeName,
        55: AdapterFloatTo16BitRange.nodeName,
        56: AdapterFloatToFloatRange.nodeName,
        57: CombineTwo8BitToSingle16Bit.nodeName,
        58: Map8BitTo16Bit.nodeName,
    }
