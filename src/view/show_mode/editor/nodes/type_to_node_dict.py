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
from view.show_mode.editor.nodes.import_node import ImportNode

type_to_node: dict[int, str] = {
        FilterTypeEnumeration.VFILTER_IMPORT: ImportNode.nodeName,
        FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN: ColorBrightnessMixinNode.nodeName,
        FilterTypeEnumeration.VFILTER_POSITION_CONSTANT: PanTiltConstant.nodeName,
        FilterTypeEnumeration.VFILTER_CUES: CueListNode.nodeName,
        FilterTypeEnumeration.VFILTER_AUTOTRACKER: AutoTrackerNode.nodeName,
        FilterTypeEnumeration.VFILTER_EFFECTSSTACK: EffectsStackNode.nodeName,
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
        FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN: TrigonometricSineNode.nodeName,
        FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN: TrigonometricCosineNode.nodeName,
        FilterTypeEnumeration.FILTER_TRIGONOMETRICS_TANGENT: TrigonometricTangentNode.nodeName,
        FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCSIN: TrigonometricArcSinNode.nodeName,
        FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCCOSIN: TrigonometricArcCosNode.nodeName,
        FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCTANGENT: TrigonometricArcTanNode.nodeName,
        FilterTypeEnumeration.FILTER_WAVES_SQUARE: SquareWaveNode.nodeName,
        FilterTypeEnumeration.FILTER_WAVES_TRIANGLE: TriangleWaveNode.nodeName,
        FilterTypeEnumeration.FILTER_WAVES_SAWTOOTH: SawtoothWaveNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM: ArithmeticLogarithmNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL: ArithmeticExponentialNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM: ArithmeticMinimumNode.nodeName,
        FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM: ArithmeticMaximumNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT: TimeNode.nodeName,
        FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_8BIT: TimeSwitchOnDelay8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_16BIT: TimeSwitchOnDelay16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_FLOAT: TimeSwitchOnDelayFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_8BIT: TimeSwitchOffDelay8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_16BIT: TimeSwitchOffDelay16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_FLOAT: TimeSwitchOffDelayFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_FADER_RAW: FaderRawNode.nodeName,
        FilterTypeEnumeration.FILTER_FADER_HSI: FaderHSINode.nodeName,
        FilterTypeEnumeration.FILTER_FADER_HSIA: FaderHSIANode.nodeName,
        FilterTypeEnumeration.FILTER_FADER_HSIU: FaderHSIUNode.nodeName,
        FilterTypeEnumeration.FILTER_FADER_HSIAU: FaderHSIAUNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_CUES: CueListNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT: Shift8BitNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_16BIT: Shift16BitNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT: ShiftFloatNode.nodeName,
        FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR: ShiftColorNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS: FaderMainBrightness.nodeName,
        FilterTypeEnumeration.FILTER_SCRIPTING_LUA: LuaFilterNode.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT: Adapter8bitToFloat.nodeName,
        FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT: Adapter16bitToFloat.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT: AdapterColorToFloatsNode.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE: AdapterFloatTo8BitRange.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE: AdapterFloatTo16BitRange.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE: AdapterFloatToRange.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT: CombineTwo8BitToSingle16Bit.nodeName,
        FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT: Map8BitTo16Bit.nodeName,
        FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE: Adapter16BitToRangeFloat.nodeName,
        FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE: Adapter8BitToRangeFloat.nodeName,
    }
