"""Sequencer channel model and interleave method enum."""

from __future__ import annotations

from enum import Enum
from logging import getLogger

from model import ColorHSI, DataType
from model.filter_data.sequencer._utils import _rf

logger = getLogger(__name__)


class InterleaveMethod(Enum):
    """Interleave Method.

    This defines the combination of values if multiple transitions are affecting the same channel at the same time.
    """

    AVERAGE = "average"
    MIN = "min"
    MAX = "max"


class SequencerChannel:
    """Model of a sequencer filter channel."""

    def __init__(self, name: str = "", dtype: DataType = DataType.DT_8_BIT) -> None:
        """Initialize the sequencer channel model.

        Args:
            name: name of the channel.
            dtype: data type of the channel.

        """
        self._name: str = name
        self._data_type: DataType = dtype
        self._default_value: int | float | ColorHSI = 0
        self._apply_default_on_empty: bool = True
        self._apply_default_on_scene_switch: bool = False
        self._interleave_method = InterleaveMethod.MAX

    @property
    def tooltip(self) -> str:
        """Tooltip for the channel."""
        return (
            f"Channel {self._name}\n"
            f"Data Type: {self._data_type.name}\n"
            f"Default Value: {self._default_value}\n"
            f"Apply Default On Empty: {self._apply_default_on_empty}\n"
            f"Apply Default on Scene Switch: {self._apply_default_on_scene_switch}\n"
            f"Interleave Method: {self._interleave_method.name}"
        )

    @property
    def data_type(self) -> DataType:
        """Data type of the channel."""
        return self._data_type

    @property
    def name(self) -> str:
        """Name of the channel."""
        return self._name

    def format_for_filter(self) -> str:
        """Serialize model into filter format."""
        default_value_str = (
            self._default_value.format_for_filter()
            if isinstance(self._default_value, ColorHSI)
            else str(self._default_value)
        )

        return (
            f"{_rf(self._name)}:{self._data_type.format_for_filters()}:{default_value_str}:"
            f"{str(self._apply_default_on_empty).lower()}:{str(self._apply_default_on_scene_switch).lower()}:"
            f"{self._interleave_method.value}"
        )

    @staticmethod
    def from_filter_str(s: str) -> SequencerChannel:
        """Parse the provided serialized string and return a new instance."""
        sc = SequencerChannel()
        if len(s or "") == 0:
            return sc
        args = s.split(":")
        sc._name = args[0]
        sc._data_type = DataType.from_filter_str(args[1])
        match sc.data_type:
            case DataType.DT_8_BIT:
                sc._default_value = max(0, min(255, int(args[2])))
            case DataType.DT_16_BIT:
                sc._default_value = max(0, min(65535, int(args[2])))
            case DataType.DT_DOUBLE:
                sc._default_value = float(args[2])
            case DataType.DT_BOOL:
                sc._default_value = max(0, min(1, int(args[2])))
            case DataType.DT_COLOR:
                sc._default_value = ColorHSI.from_filter_str(args[2])
            case _:
                logger.error("Expected data type: %s", sc.data_type)
        sc._apply_default_on_empty = args[3].lower() == "true"
        sc._apply_default_on_scene_switch = args[4].lower() == "true"
        sc._interleave_method = InterleaveMethod(args[5])
        return sc

    def copy(self) -> SequencerChannel:
        """Copy the current instance."""
        sc = SequencerChannel()
        sc._name = self._name
        sc._data_type = self._data_type
        if self._data_type == DataType.DT_COLOR:
            sc._default_value = self._default_value.copy()
        else:
            sc._default_value = self._default_value
        sc._apply_default_on_empty = self._apply_default_on_empty
        sc._apply_default_on_scene_switch = self._apply_default_on_scene_switch
        sc._interleave_method = self._interleave_method
        return sc
