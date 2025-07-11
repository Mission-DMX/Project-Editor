# coding=utf-8
from abc import ABC, abstractmethod
from ctypes import ArgumentError
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING

from model import ColorHSI, DataType
from model.filter_data.transfer_function import TransferFunction
from model.filter_data.utility import format_seconds

if TYPE_CHECKING:
    pass

logger = getLogger(__file__)


class EndAction(Enum):
    HOLD = 0
    START_AGAIN = 1
    NEXT = 2

    def __str__(self):
        if self.value == EndAction.HOLD.value:
            return "Hold current values"
        if self.value == EndAction.NEXT.value:
            return "Jump to next cue"
        if self.value == EndAction.START_AGAIN.value:
            return "Restart cue"

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
        self._transition_type: str = transition_type
        self._value = None

    @property
    def transition(self):
        return self._transition_type

    @transition.setter
    def transition(self, new_value: str):
        if new_value not in ["edg", "lin", "sig", "e_i", "e_o"]:
            raise ArgumentError(f"Unsupported transition type: {new_value}")
        self._transition_type = new_value

    @abstractmethod
    def encode(self) -> str:
        """This method returns the state encodes in the filter format"""
        raise NotImplementedError()

    @abstractmethod
    def decode(self, content: str):
        """This method decodes the state configuration from a filter config string."""
        raise NotImplementedError()

    @abstractmethod
    def get_data_type(self) -> DataType:
        """This method needs to return the filter data type."""
        raise NotImplementedError()

    @abstractmethod
    def copy(self) -> "State":
        """This method needs to return a copy of the state"""
        raise NotImplementedError()


class StateEightBit(State):

    def copy(self) -> "State":
        s = StateEightBit(self._transition_type)
        s._value = self._value
        return s

    def __init__(self, transition_type: str):
        super().__init__(transition_type)
        self._value = 0

    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        return f"{int(self._value)}@{self._transition_type}"

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
    def copy(self) -> "State":
        s = StateSixteenBit(self._transition_type)
        s._value = self._value
        return s

    def __init__(self, transition_type: str):
        super().__init__(transition_type)
        self._value = 0

    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        return f"{int(self._value)}@{self._transition_type}"

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
    def copy(self) -> "State":
        s = StateDouble(self._transition_type)
        s._value = self._value
        return s

    def __init__(self, transition_type: str):
        super().__init__(transition_type)
        self._value = 0.0

    def encode(self) -> str:
        return f"{float(self._value)}@{self._transition_type}"

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = float(c_arr[0])
        self._transition_type = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_DOUBLE


class StateColor(State):
    def copy(self) -> "State":
        s = StateColor(self._transition_type)
        s._value = self._value.copy()
        return s

    def __init__(self, transition_type: str):
        super().__init__(transition_type)
        self._value = ColorHSI(180.0, 0.0, 0.0)

    def encode(self) -> str:
        return f"{self._value.format_for_filter()}@{self._transition_type}"

    def decode(self, content: str):
        c_arr = content.split("@")
        self._value = ColorHSI.from_filter_str(c_arr[0])
        self._transition_type = c_arr[1]

    def get_data_type(self) -> DataType:
        return DataType.DT_COLOR

    @property
    def color(self) -> ColorHSI:
        return self._value

    @color.setter
    def color(self, value: ColorHSI):
        self._value = value


class KeyFrame:
    def __init__(self, parent_cue: "Cue"):
        self._states: list[State] = []
        self.timestamp: float = 0.0
        self._parent = parent_cue
        self.only_on_channel: str | None = None

    def get_data_types(self) -> list[DataType]:
        l = []
        for s in self._states:
            l.append(s.get_data_type())
        return l

    def format_filter_str(self) -> str:
        return f"{self.timestamp}:{"&".join([s.encode() for s in self._states])}"

    @staticmethod
    def from_format_str(f_str: str, channel_data_types: list[tuple[str, DataType]], parent_cue: "Cue"):
        parts = f_str.split(':')
        if len(parts) != 2:
            raise ArgumentError("A keyframe definition should contain exactly two elements")
        f = KeyFrame(parent_cue)
        f.timestamp = float(parts[0])
        i = 0
        for state_dev in parts[1].split('&'):
            state_dev_parts = state_dev.split('@')
            if i >= len(channel_data_types):
                if i == 0 and len(channel_data_types) == 0:
                    return None
                raise ArgumentError("There are more elements in the key frame than channel data types")
            dt = channel_data_types[i][1]
            match dt:
                case DataType.DT_COLOR:
                    s_entry = StateColor(state_dev_parts[1])
                case DataType.DT_8_BIT:
                    s_entry = StateEightBit(state_dev_parts[1])
                case DataType.DT_16_BIT:
                    s_entry = StateSixteenBit(state_dev_parts[1])
                case DataType.DT_DOUBLE:
                    s_entry = StateDouble(state_dev_parts[1])
                case _:
                    raise ArgumentError(f"Unsupported filter data type: {state_dev_parts[1]}")
            s_entry.decode(state_dev)
            f._states.append(s_entry)
            i += 1
        return f

    def append_state(self, s: State):
        if s is not None:
            self._states.append(s)

    def delete_from_parent_cue(self):
        """This method deletes the frame from the parent."""
        self._parent._frames.remove(self)

    def copy(self, new_parent: "Cue") -> "KeyFrame":
        kf = KeyFrame(new_parent)
        kf.timestamp = self.timestamp
        for s in self._states:
            kf._states.append(s.copy())
        return kf


class Cue:
    def __init__(self, definition: str | None = None):
        self.end_action = EndAction.HOLD
        self._frames: list[KeyFrame] = []
        self._channel_definitions: list[tuple[str, DataType]] = []
        self.restart_on_another_play_press: bool = False
        self.index_in_editor = 0
        self.name: str = ""
        if definition is not None:
            self.from_string_definition(definition)

    @property
    def duration(self) -> float:
        """Computes the length of the cue"""
        latest_timestamp = 0.0
        for f in self._frames:
            latest_timestamp = max(latest_timestamp, f.timestamp)
        return latest_timestamp

    @property
    def duration_formatted(self) -> str:
        """Returns the duration of the cue as a formatted string."""
        return format_seconds(self.duration)

    @property
    def channel_types(self) -> list[DataType]:
        """Returns the keyframe data types"""
        if len(self._frames) == 0:
            return []

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
        if self.name is None or self.name == "":
            self.name = "No Name"
        return (f"{"|".join(frames_str_list)}#{end_handling_str}#"
                f"{restart_beh_str}#{self.name.replace('#', '')}")

    def from_string_definition(self, definition: str):
        primary_tokens = definition.split("#")
        frame_definitions = primary_tokens[0].split("|")
        for frame_dev in frame_definitions:
            if frame_dev:
                frame_pt = KeyFrame.from_format_str(frame_dev, self._channel_definitions, self)
                if frame_pt is None:
                    logger.error("Got empty Keyframe while parsing.")
                else:
                    self._frames.append(frame_pt)
        if len(primary_tokens) > 1:
            self.end_action = EndAction.from_format_str(primary_tokens[1])
        if len(primary_tokens) > 2:
            self.restart_on_another_play_press = primary_tokens[2] == "restart"
        if len(primary_tokens) > 3:
            self.name = primary_tokens[3]

    def add_channel(self, name: str, t: str | DataType):
        """Add a channel name to list of names"""
        if isinstance(t, str):
            dt = DataType.from_filter_str(t)
        else:
            dt = t
        for cd in self._channel_definitions:
            if cd[0] == name:
                if cd[1] == dt:
                    return

                raise ValueError("This channel name already exists with a different data type.")
        self._channel_definitions.append((name, dt))
        for kf in self._frames:
            match dt:
                case DataType.DT_COLOR:
                    kf_s = StateColor(TransferFunction.EDGE.value)
                case DataType.DT_8_BIT:
                    kf_s = StateEightBit(TransferFunction.EDGE.value)
                case DataType.DT_DOUBLE:
                    kf_s = StateDouble(TransferFunction.EDGE.value)
                case DataType.DT_16_BIT:
                    kf_s = StateSixteenBit(TransferFunction.EDGE.value)
                case _:
                    kf_s = StateEightBit(TransferFunction.EDGE.value)
            kf._states.append(kf_s)

    def insert_frame(self, f: KeyFrame):
        """Add a frame to the cue"""
        self._frames.append(f)

    def remove_channel(self, c: "ExternalChannelDefinition | tuple[str, DataType]"):
        target_index = -1
        if isinstance(c, tuple):
            name = c[0]
        else:
            name = c.name
        for i in range(len(self._channel_definitions)):
            if self._channel_definitions[i][0] == name:
                self._channel_definitions.pop(i)
                target_index = i
                break
        if target_index == -1:
            return
        for f in self._frames:
            f._states.pop(target_index)

    def copy(self) -> "Cue":
        c = Cue()
        c.end_action = self.end_action
        for kf in self._frames:
            c._frames.append(kf.copy(c))
        for cd in self._channel_definitions:
            c._channel_definitions.append((cd[0], cd[1]))
        c.name = f"{self.name} (copy)"
        c.restart_on_another_play_press = self.restart_on_another_play_press
        return c
