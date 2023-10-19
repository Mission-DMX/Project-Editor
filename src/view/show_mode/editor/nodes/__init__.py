"""Module containing and exporting all available filter nodes"""
from .filternode import FilterNode
from .constants import *
from .debug import *
from .adapters import *
from .arithmetics import *
from .trigonometics import *
from .waves import *
from .time import *
from .faders import *
from .effects import *
from .universenode import UniverseNode
from .scripting import *

type_to_node: dict[int, str] = {
        0: Constants8BitNode.nodeName,
        1: Constants16BitNode.nodeName,
        2: ConstantsFloatNode.nodeName,
        3: ConstantsColorNode.nodeName,
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
        32: TimeNode.nodeName,
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
        49: FaderMainBrightness.nodeName,
        50: LuaFilterNode.nodeName,
        51: Adapter8bitToFloat.nodeName,
        52: Adapter16bitToFloat.nodeName,
    }
