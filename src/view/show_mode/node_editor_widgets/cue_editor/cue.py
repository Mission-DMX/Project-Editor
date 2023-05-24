from abc import ABC, abstractmethod
from enum import Enum

from model import DataType, ColorHSI
from view.show_mode.node_editor_widgets.cue_editor.utility import format_seconds


class EndAction(Enum):
    HOLD = 0
    START_AGAIN = 1
    NEXT = 2

    def __str__(self):
        if self.value == EndAction.HOLD:
            return "Hold current values"
        elif self.value == EndAction.NEXT:
            return "Jump to next cue"
        elif self.value == EndAction.START_AGAIN:
            return "Restart cue"
        else:
            return "Unknown action"

    @property
    def formatted_value_list(self) -> list[str]:
        return [str(a) for a in [EndAction.HOLD, EndAction.START_AGAIN, EndAction.NEXT]]


class State(ABC):

    def __init__(self, channel_name: str):
        self._channel_name = channel_name

    @abstractmethod
    def encode(self) -> str:
        """This method returns the state encodes in the filter format"""
        raise NotImplementedError

    @abstractmethod
    def decode(self, content: str):
        """This method decodes the state configuration from a filter config string."""
        raise NotImplementedError

    @abstractmethod
    def get_data_type(self) -> DataType:
        """This method needs to return the filter data type."""
        raise NotImplementedError


class StateEightBit(State):

    def __init__(self, channel_name: str):
        super().__init__(channel_name)
        self._value = 0

    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        return "{}@{}".format(int(self._value), self._channel_name)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = int(c_arr[0])
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        self._channel_name = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_8_BIT


class StateSixteenBit(State):
    def __init__(self, channel_name: str):
        super.__init__(channel_name)
        self._value = 0

    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        return "{}@{}".format(int(self._value), self._channel_name)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = int(c_arr[0])
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        self._channel_name = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_16_BIT


class StateDouble(State):
    def __init__(self, channel_name: str):
        super.__init__(channel_name)
        self._value = 0.0

    def encode(self) -> str:
        return "{}@{}".format(float(self._value), self._channel_name)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = float(c_arr[0])
        self._channel_name = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_DOUBLE


class StateColor(State):
    def __init__(self, channel_name: str):
        super.__init__(channel_name)
        self._value = ColorHSI(180.0, 0.0, 0.0)

    def encode(self) -> str:
        return "{}@{}".format(self._value.format_for_filter(), self._channel_name)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = ColorHSI(c_arr[0])
        self._channel_name = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_COLOR


class KeyFrame:
    def __init__(self):
        self._states: list[State] = []

    def get_data_types(self) -> list[DataType]:
        l = []
        for s in self._states:
            l.append(s.get_data_type())
        return l


class Cue:
    def __init__(self):
        self.end_action = EndAction.HOLD
        self._frames: list[KeyFrame] = []

    @property
    def duration(self) -> float:
        """Computes the length of the cue"""
        # TODO implement
        return 0.0

    @property
    def duration_formatted(self) -> str:
        """Returns the duration of the cue as a formatted string."""
        return format_seconds(self.duration)

    @property
    def channel_types(self) -> list[DataType]:
        """Returns the keyframe data types"""
        if len(self._frames) == 0:
            return []
        else:
            return self._frames[0].get_data_types()

