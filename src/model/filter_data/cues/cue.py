"""Cue filter model.

EndAction
State -- Abstract State.
StateEightBit -- 8 bit state.
StateSixteenBit -- 16 bit state.
StateDouble  -- float state.
StateColor -- Color state.
KeyFrame -- Model of a key frame.
Cue -- Cue filter model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from ctypes import ArgumentError
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING, Never, Union, override

from model import ColorHSI, DataType
from model.filter_data.transfer_function import TransferFunction
from model.filter_data.utility import format_seconds

if TYPE_CHECKING:
    from view.show_mode.editor.node_editor_widgets.cue_editor.cue_editor_widget import ExternalChannelDefinition

logger = getLogger(__name__)


class EndAction(Enum):
    """Enum describing what should happen at the end of a cue."""

    HOLD = 0
    START_AGAIN = 1
    NEXT = 2

    def __str__(self) -> str:
        """Get human readable string representation."""
        match self:
            case EndAction.HOLD:
                return "Hold current values"
            case EndAction.START_AGAIN:
                return "Jump to next cue"
            case _:
                return "Restart cue"

        return "Unknown action"

    @staticmethod
    def formatted_value_list() -> list[str]:
        """Get possible enum values as list of human readable strings."""
        return [str(a) for a in [EndAction.HOLD, EndAction.START_AGAIN, EndAction.NEXT]]

    def get_filter_format_str(self) -> str:
        """Serialize for filter string."""
        match self:
            case EndAction.HOLD:
                return "hold"
            case EndAction.START_AGAIN:
                return "start_again"
            case _:
                return "next_cue"

    @staticmethod
    def from_format_str(f_str: str) -> EndAction:
        """Deserialize from filter string."""
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
    """Abstract representation of a state in a cue."""

    def __init__(self, transition_type: str) -> None:
        """Initialize state using given transition type."""
        self._transition_type: str = transition_type
        self._value = None

    @property
    def transition(self) -> str:
        """Get or set the transition from the last state."""
        return self._transition_type

    @transition.setter
    def transition(self, new_value: str) -> None:
        if new_value not in ["edg", "lin", "sig", "e_i", "e_o"]:
            raise ArgumentError(f"Unsupported transition type: {new_value}")
        self._transition_type = new_value

    @abstractmethod
    def encode(self) -> str:
        """Get the state encodes in the filter format."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, content: str) -> Never:
        """Get the state configuration from a filter config string."""
        raise NotImplementedError

    @abstractmethod
    def get_data_type(self) -> DataType:
        """Get the filter data type."""
        raise NotImplementedError

    @abstractmethod
    def copy(self) -> State:
        """Get a copy of the state."""
        raise NotImplementedError


class StateEightBit(State):
    """State for 8bit channel."""

    @override
    def copy(self) -> State:
        """Get a copy of this state."""
        s = StateEightBit(self._transition_type)
        s._value = self._value
        return s

    def __init__(self, transition_type: str) -> None:
        """Initialize state using given transition type."""
        super().__init__(transition_type)
        self._value = 0

    @override
    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        return f"{int(self._value)}@{self._transition_type}"

    @override
    def decode(self, content: str) -> None:
        c_arr = content.split("@")
        self._value = int(c_arr[0])
        if self._value < 0:
            self._value = 0
        elif self._value > 255:
            self._value = 255
        self._transition_type = c_arr[1]

    @override
    def get_data_type(self) -> DataType:
        return DataType.DT_8_BIT


class StateSixteenBit(State):
    """State for sixteen bit channel."""

    @override
    def copy(self) -> State:
        s = StateSixteenBit(self._transition_type)
        s._value = self._value
        return s

    def __init__(self, transition_type: str) -> None:
        """Initialize state using given transition type."""
        super().__init__(transition_type)
        self._value = 0

    @override
    def encode(self) -> str:
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        return f"{int(self._value)}@{self._transition_type}"

    @override
    def decode(self, content: str) -> None:
        c_arr = content.split("@")
        self._value = int(c_arr[0])
        if self._value < 0:
            self._value = 0
        elif self._value > 65535:
            self._value = 65535
        self._transition_type = c_arr[1]

    @override
    def get_data_type(self) -> DataType:
        return DataType.DT_16_BIT


class StateDouble(State):
    """State for double channel."""

    @override
    def copy(self) -> State:
        s = StateDouble(self._transition_type)
        s._value = self._value
        return s

    def __init__(self, transition_type: str) -> None:
        """Initialize state using given transition type."""
        super().__init__(transition_type)
        self._value = 0.0

    @override
    def encode(self) -> str:
        return f"{float(self._value)}@{self._transition_type}"

    @override
    def decode(self, content: str) -> None:
        c_arr = content.split("@")
        self._value = float(c_arr[0])
        self._transition_type = c_arr[1]

    @override
    def get_data_type(self) -> DataType:
        return DataType.DT_DOUBLE


class StateColor(State):
    """State for color channel."""

    @override
    def copy(self) -> State:
        s = StateColor(self._transition_type)
        s._value = self._value.copy()
        return s

    def __init__(self, transition_type: str) -> None:
        """Initialize state using given transition type."""
        super().__init__(transition_type)
        self._value = ColorHSI(180.0, 0.0, 0.0)

    @override
    def encode(self) -> str:
        return f"{self._value.format_for_filter()}@{self._transition_type}"

    @override
    def decode(self, content: str) -> None:
        c_arr = content.split("@")
        self._value = ColorHSI.from_filter_str(c_arr[0])
        self._transition_type = c_arr[1]

    @override
    def get_data_type(self) -> DataType:
        return DataType.DT_COLOR

    @property
    def color(self) -> ColorHSI:
        """Get or set color of this state."""
        return self._value

    @color.setter
    def color(self, value: ColorHSI) -> None:
        self._value = value


class KeyFrame:
    """Model of a key frame."""

    def __init__(self, parent_cue: Cue) -> None:
        """Initialize key frame using a given parent cue."""
        self._states: list[State] = []
        self.timestamp: float = 0.0
        self._parent = parent_cue
        self.only_on_channel: str | None = None

    def get_data_types(self) -> list[DataType]:
        """Get data types of associated channels."""
        return [s.get_data_type() for s in self._states]

    def format_filter_str(self) -> str:
        """Serialize for filter."""
        return f"{self.timestamp}:{"&".join([s.encode() for s in self._states])}"

    @staticmethod
    def from_format_str(f_str: str, channel_data_types: list[tuple[str, DataType]], parent_cue: Cue) -> KeyFrame:
        """Deserialize from filter representation.

        :param f_str: Filter representation string.
        :param channel_data_types: Associated channels.
        :param parent_cue: Parent cue.
        """
        parts = f_str.split(":")
        if len(parts) != 2:
            raise ArgumentError("A keyframe definition should contain exactly two elements")
        f = KeyFrame(parent_cue)
        f.timestamp = float(parts[0])

        for i, state_dev in enumerate(parts[1].split("&")):
            state_dev_parts = state_dev.split("@")
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

        return f

    def append_state(self, s: State) -> None:
        """Add a state to this frame."""
        if s is not None:
            self._states.append(s)

    def delete_from_parent_cue(self) -> None:
        """Delete the frame from the parent."""
        self._parent._frames.remove(self)

    def copy(self, new_parent: Cue) -> KeyFrame:
        """Copy the object."""
        kf = KeyFrame(new_parent)
        kf.timestamp = self.timestamp
        for s in self._states:
            kf._states.append(s.copy())
        return kf


class Cue:
    """Model of a cue from a cue filter."""

    def __init__(self, definition: str | None = None) -> None:
        """Initialize cue model."""
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
        """Computes the length of the cue."""
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
        """Returns the keyframe data types."""
        if len(self._frames) == 0:
            return []

        return self._frames[0].get_data_types()

    @property
    def channels(self) -> list[tuple[str, DataType]]:
        """Returns the nominal channel definitions."""
        return list(self._channel_definitions)

    def format_cue(self) -> str:
        """Returns the cue formatted in the filter config format."""
        end_handling_str = self.end_action.get_filter_format_str()
        restart_beh_str = "restart" if self.restart_on_another_play_press else "do_nothing"
        frames_str_list = [f.format_filter_str() for f in self._frames]
        if self.name is None or self.name == "":
            self.name = "No Name"
        return (f"{"|".join(frames_str_list)}#{end_handling_str}#"
                f"{restart_beh_str}#{self.name.replace('#', '')}")

    def from_string_definition(self, definition: str) -> None:
        """Deserialize filter definition."""
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

    def add_channel(self, name: str, t: str | DataType) -> None:
        """Add a channel name to list of names."""
        dt = DataType.from_filter_str(t) if isinstance(t, str) else t

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

    def insert_frame(self, f: KeyFrame) -> None:
        """Add a frame to the cue."""
        self._frames.append(f)

    def remove_channel(self, c: Union[ExternalChannelDefinition, tuple[str, DataType]]) -> None:
        """Remove the specified channel from the model."""
        target_index = -1
        name = c[0] if isinstance(c, tuple) else c.name
        for i in range(len(self._channel_definitions)):
            if self._channel_definitions[i][0] == name:
                self._channel_definitions.pop(i)
                target_index = i
                break
        if target_index == -1:
            return
        for f in self._frames:
            f._states.pop(target_index)

    def copy(self) -> Cue:
        """Get a copy of the object."""
        c = Cue()
        c.end_action = self.end_action
        for kf in self._frames:
            c._frames.append(kf.copy(c))
        for cd in self._channel_definitions:
            c._channel_definitions.append((cd[0], cd[1]))
        c.name = f"{self.name} (copy)"
        c.restart_on_another_play_press = self.restart_on_another_play_press
        return c
