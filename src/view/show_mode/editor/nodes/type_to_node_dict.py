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
        FilterTypeEnumeration.VFILTER_POSITION_CONSTANT: PanTiltConstant.nodeName,
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
        FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_16BIT: ArithmeticFloatTo16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT: ArithmeticFloatTo8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_ROUND: ArithmeticRoundNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB: AdapterColorToRGBNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW: AdapterColorToRGBWNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBWA: AdapterColorToRGBWANode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR: AdapterFloatToColorNode.nodeName,
        19: TrigonometricSineNode.nodeName,
        20: TrigonometricCosineNode.nodeName,
        21: TrigonometricTangentNode.nodeName,
        22: TrigonometricArcSinNode.nodeName,
        23: TrigonometricArcCosNode.nodeName,
        24: TrigonometricArcTanNode.nodeName,
        25: SquareWaveNode.nodeName,
        26: TriangleWaveNode.nodeName,
        27: SawtoothWaveNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM: ArithmeticLogarithmNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL: ArithmeticExponentialNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM: ArithmeticMinimumNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM: ArithmeticMaximumNode.nodeName,
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
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT: Shift8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_16BIT: Shift16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT: ShiftFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR: ShiftColorNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS: FaderMainBrightness.nodeName,
        50: LuaFilterNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT: Adapter8bitToFloat.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT: Adapter16bitToFloat.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT: AdapterColorToFloatsNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE: AdapterFloatTo8BitRange.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE: AdapterFloatTo16BitRange.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE: AdapterFloatToFloatRange.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT: CombineTwo8BitToSingle16Bit.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT: Map8BitTo16Bit.nodeName,
    }
