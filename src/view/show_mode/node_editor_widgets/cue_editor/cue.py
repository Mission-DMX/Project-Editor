from abc import ABC, abstractmethod
from ctypes import ArgumentError
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

    @staticmethod
    def formatted_value_list() -> list[str]:
        return [str(a) for a in [EndAction.HOLD, EndAction.START_AGAIN, EndAction.NEXT]]

    def get_filter_format_str(self) -> str:
        if self.value == EndAction.HOLD.value:
            return "hold"
        elif self.value == EndAction.START_AGAIN.value:
            return "start_again"
        else:
            return "next_cue"

    @staticmethod
    def from_format_str(f_str: str):
        match f_str:
            case "start_again":
                return EndAction.START_AGAIN
            case "next_cue":
                return EndAction.NEXT
            case "hold":
                return EndAction.HOLD
            case _:
                return EndAction.HOLD


class State(ABC):

    def __init__(self, transition_type: str):
        self._transition_type = transition_type

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

    def __init__(self, transition_type: str):
        super().__init__(transition_type)
        self._value = 0

    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        return "{}@{}".format(int(self._value), self._transition_type)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = int(c_arr[0])
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        self._transition_type = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_8_BIT


class StateSixteenBit(State):
    def __init__(self, transition_type: str):
        super.__init__(transition_type)
        self._value = 0

    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        return "{}@{}".format(int(self._value), self._transition_type)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = int(c_arr[0])
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        self._transition_type = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_16_BIT


class StateDouble(State):
    def __init__(self, transition_type: str):
        super.__init__(transition_type)
        self._value = 0.0

    def encode(self) -> str:
        return "{}@{}".format(float(self._value), self._transition_type)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = float(c_arr[0])
        self._transition_type = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_DOUBLE


class StateColor(State):
    def __init__(self, transition_type: str):
        super.__init__(transition_type)
        self._value = ColorHSI(180.0, 0.0, 0.0)

    def encode(self) -> str:
        return "{}@{}".format(self._value.format_for_filter(), self._transition_type)

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = ColorHSI(c_arr[0])
        self._transition_type = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_COLOR


class KeyFrame:
    def __init__(self):
        self._states: list[State] = []
        self.timestamp: float = 0.0

    def get_data_types(self) -> list[DataType]:
        l = []
        for s in self._states:
            l.append(s.get_data_type())
        return l

    def format_filter_str(self) -> str:
        return "{}:{}".format(self.timestamp, "&".join([s.encode() for s in self._states]))

    @staticmethod
    def from_format_str(f_str: str):
        parts = f_str.split(':')
        if len(parts) != 2:
            raise ArgumentError("A keyframe definition should contain exactly two elements")
        f = KeyFrame()
        f.timestamp = float(parts[0])
        for state_dev in parts[1].split('&'):
            state_dev_parts = state_dev.split('@')
            match state_dev_parts[1]:
                case "color":
                    s_entry = StateColor()
                case "8bit":
                    s_entry = StateEightBit()
                case "16bit":
                    s_entry = StateSixteenBit()
                case "float":
                    s_entry = StateDouble()
                case _:
                    raise ArgumentError("Unsupported filter data type: {}".format(state_dev_parts[1]))
            f._states.append(s_entry.decode(state_dev))


class Cue:
    def __init__(self):
        self.end_action = EndAction.HOLD
        self._frames: list[KeyFrame] = []
        self._channel_definitions: list[tuple[str, DataType]] = []
        self.restart_on_another_play_press: bool = False

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

    @property
    def channels(self) -> list[tuple[str, DataType]]:
        """Returns the nominal channel definitions"""
        return list(self._channel_definitions)

    def format_cue(self) -> str:
        """This method returns the cue formatted in the filter config format."""
        end_handling_str = self.end_action.get_filter_format_str()
        restart_beh_str = "restart" if self.restart_on_another_play_press else "do_nothing"
        frames_str_list = [f.format_filter_str() for f in self._frames]
        "{}#{}#{}".format("|".join(frames_str_list), end_handling_str, restart_beh_str)

    def from_string_definition(self, definition: str):
        primary_tokens = definition.split("#")
        frame_definitions = primary_tokens[0].split("|")
        for frame_dev in frame_definitions:
            self._frames.append(KeyFrame.from_format_str(frame_dev))
        if len(primary_tokens) > 1:
            self.end_action = EndAction.from_format_str(primary_tokens[1])
        if len(primary_tokens) > 2:
            self.restart_on_another_play_press = primary_tokens[2] == "restart"

    def add_channel(self, name: str, type_str: str):
        """Add a channel name to list of names"""
        self._channel_definitions.append((name, DataType.from_filter_str(type_str)))

