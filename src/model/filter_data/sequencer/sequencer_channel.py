from enum import Enum

from model import DataType, ColorHSI


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

        return (f"{self.name}:{self.data_type.format_for_filters()}:{default_value_str}:"
                f"{str(self.apply_default_on_empty).lower()}:{str(self.apply_default_on_scene_switch).lower()}:"
                f"{self.interleave_method.value}")
