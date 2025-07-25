"""Module containing and exporting all available filter nodes"""
from model.filter import FilterTypeEnumeration
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
from view.show_mode.editor.nodes.impl.color_manip_nodes import (
                                                       ColorMixerAdditiveRGBNode,
                                                       ColorMixerHSVNode,
                                                       ColorMixerNormativeRGBNode,
                                                       ColorMixerVFilterNode,
)
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

type_to_node: dict[int, str] = {
    FilterTypeEnumeration.VFILTER_COLOR_MIXER: ColorMixerVFilterNode.nodeName,
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
    FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV: ColorMixerHSVNode.nodeName,
    FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB: ColorMixerAdditiveRGBNode.nodeName,
    FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATVE_RGB: ColorMixerNormativeRGBNode.nodeName,
    FilterTypeEnumeration.FILTER_SUM_8BIT: Sum8BitNode.nodeName,
    FilterTypeEnumeration.FILTER_SUM_16BIT: Sum16BitNode.nodeName,
    FilterTypeEnumeration.FILTER_SUM_FLOAT: SumFloatNode.nodeName,
    FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT: DebugRemote8BitNode.nodeName,
    FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT: DebugRemote16BitNode.nodeName,
    FilterTypeEnumeration.FILTER_REMOTE_DEBUG_FLOAT: DebugRemoteFloatNode.nodeName,
    FilterTypeEnumeration.FILTER_REMOTE_DEBUG_PIXEL: DebugRemoteColorNode.nodeName,
}
