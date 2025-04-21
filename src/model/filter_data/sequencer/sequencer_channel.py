from enum import Enum
from logging import getLogger

from model import ColorHSI, DataType
from model.filter_data.sequencer._utils import _rf

logger = getLogger(__file__)


class InterleaveMethod(Enum):
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"


class SequencerChannel:
    def __init__(self, name: str = "", dtype: DataType = DataType.DT_8_BIT):
        self.name: str = name
        self.data_type = dtype
        self.default_value: int | float | ColorHSI = 0
        self.apply_default_on_empty: bool = True
        self.apply_default_on_scene_switch: bool = False
        self.interleave_method = InterleaveMethod.MAX

    def format_for_filter(self) -> str:
        default_value_str = self.default_value.format_for_filter() if isinstance(self.default_value, ColorHSI) else str(self.default_value)

        return (f"{_rf(self.name)}:{self.data_type.format_for_filters()}:{default_value_str}:"
                f"{str(self.apply_default_on_empty).lower()}:{str(self.apply_default_on_scene_switch).lower()}:"
                f"{self.interleave_method.value}")

    @staticmethod
    def from_filter_str(s: str) -> "SequencerChannel":
        """
        Parse the provided serialized string and return a new instance.
        """
        sc = SequencerChannel()
        if len(s or "") == 0:
            return sc
        args = s.split(":")
        sc.name = args[0]
        sc.data_type = DataType.from_filter_str(args[1])
        match sc.data_type:
            case DataType.DT_8_BIT:
                sc.default_value = max(0, min(255, int(args[2])))
            case DataType.DT_16_BIT:
                sc.default_value = max(0, min(65535, int(args[2])))
            case DataType.DT_DOUBLE:
                sc.default_value = float(args[2])
            case DataType.DT_BOOL:
                sc.default_value = max(0, min(1, int(args[2])))
            case DataType.DT_COLOR:
                sc.default_value = ColorHSI.from_filter_str(args[2])
            case _:
                logger.error("Execpected data type: {}", sc.data_type)
        sc.apply_default_on_empty = args[3].lower() == "true"
        sc.apply_default_on_scene_switch = args[4].lower() == "true"
        sc.interleave_method = InterleaveMethod(args[5])
        return sc

    def copy(self) -> "SequencerChannel":
        sc = SequencerChannel()
        sc.name = self.name
        sc.data_type = self.data_type
        if self.data_type == DataType.DT_COLOR:
            sc.default_value = self.default_value.copy()
        else:
            sc.default_value = self.default_value
        sc.apply_default_on_empty = self.apply_default_on_empty
        sc.apply_default_on_scene_switch = self.apply_default_on_scene_switch
        sc.interleave_method = self.interleave_method
        return sc
