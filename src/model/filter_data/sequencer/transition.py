"""Transition model.

SequenceKeyFrame -- A sequence key frame.
Transition -- A set of key frames, executed in order.
"""

from __future__ import annotations

from collections import Counter
from logging import getLogger
from types import MappingProxyType
from typing import TYPE_CHECKING

from model import ColorHSI, DataType
from model.filter_data.cues.cue import Cue, KeyFrame, State, StateColor, StateDouble, StateEightBit, StateSixteenBit
from model.filter_data.sequencer._utils import _rf
from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from collections.abc import Sequence

    from model.filter_data.sequencer.sequencer_channel import SequencerChannel


logger = getLogger(__name__)


class SequenceKeyFrame:
    """A sequence key frame."""

    def __init__(self, target_channel: SequencerChannel) -> None:
        """Initialize a sequence key frame.

        Args:
            target_channel: Target channel.

        """
        if target_channel is None:
            logger.error("target_channel is None")
        self._channel: SequencerChannel = target_channel
        self._target_value: int | float | ColorHSI = 0
        self._duration: float = 0.0
        self._tf: TransferFunction = TransferFunction.LINEAR

    @property
    def duration(self) -> float:
        """Duration of this key frame."""
        return self._duration

    @property
    def channel(self) -> SequencerChannel:
        """Target channel."""
        return self._channel

    def format_for_filter(self) -> str:
        """Serialize for filter definition."""
        value_str: str = (
            self._target_value.format_for_filter()
            if isinstance(self._target_value, ColorHSI)
            else str(self._target_value)
        )
        return f"{_rf(self._channel.name)}:{value_str}:{self._tf.value}:{self._duration * 1000.0}"

    @staticmethod
    def from_filter_str(s: str, channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> SequenceKeyFrame:
        """Deserialize from filter definition.

        Args:
            s: Filter definition.
            channels: Channels to map to.

        """
        args = s.split(":")
        channel_name = args[0]
        found_channel: SequencerChannel | None = None
        if isinstance(channels, list):
            for c in channels:
                if c.name == channel_name:
                    found_channel = c
        else:
            found_channel = channels.get(channel_name)
        if found_channel is None:
            raise ValueError("Requested channel {} was not found.", channel_name)
        skf = SequenceKeyFrame(found_channel)
        match found_channel.data_type:
            case DataType.DT_8_BIT:
                skf._target_value = max(0, min(255, int(args[1])))
            case DataType.DT_16_BIT:
                skf._target_value = max(0, min(65535, int(args[1])))
            case DataType.DT_DOUBLE:
                skf._target_value = float(args[1])
            case DataType.DT_BOOL:
                skf._target_value = max(0, min(1, int(args[1])))
            case DataType.DT_COLOR:
                skf._target_value = ColorHSI.from_filter_str(args[1])
            case _:
                logger.error("Expected data type: %s", found_channel.data_type)
        skf._duration = float(args[3]) / 1000.0
        skf._tf = TransferFunction(args[2])
        return skf

    def copy(self, new_target: SequencerChannel) -> SequenceKeyFrame:
        """Get a copy of this sequence key frame.

        Args:
            new_target: The parent channel of the new key frame object.

        """
        if self._channel.name != new_target.name or self._channel == new_target:
            logger.warning("Expected copy of own channel for generation.")
        sc = SequenceKeyFrame(new_target)
        if self._channel.data_type == DataType.DT_COLOR:
            sc._target_value = self._target_value.copy()
        else:
            sc._target_value = self._target_value
        sc._duration = self._duration
        sc._tf = self._tf
        return sc

    def target_value_as_cue_state(self) -> State:
        """Return the target value as a cue state."""
        match self._channel.data_type:
            case DataType.DT_8_BIT:
                s = StateEightBit(self._tf.value)
            case DataType.DT_16_BIT:
                s = StateSixteenBit(self._tf.value)
            case DataType.DT_DOUBLE:
                s = StateDouble(self._tf.value)
            case DataType.DT_COLOR:
                s = StateColor(self._tf.value)
            case DataType.DT_BOOL:
                s = StateEightBit(self._tf.value)
        s._value = self._target_value
        return s


def _force_channel_dict(cd: list[SequencerChannel] | dict[str, SequencerChannel]) -> dict[str, SequencerChannel]:
    if isinstance(cd, dict):
        return cd
    new_dict = {}
    for c in cd:
        new_dict[c.name] = c
    return new_dict


class Transition:
    """Represents a transition to be applied to channels within a sequencer filter."""

    def __init__(self) -> None:
        """Instantiate a transition object."""
        self._trigger_event: tuple[int, int, str] = (0, 0, "")
        self._frames: list[SequenceKeyFrame] = []
        self._name: str = ""
        self._preselected_channels: dict[str, DataType] = {}

    @property
    def preselected_channels(self) -> MappingProxyType[str, DataType]:
        """Preselected channels."""
        return MappingProxyType(self._preselected_channels)

    @preselected_channels.setter
    def preselected_channels(self, new_preselected_channels: dict[str, DataType]) -> None:
        self._preselected_channels = new_preselected_channels

    def update_preselected_channels(self, new_preselected_channels: dict[str, DataType]) -> None:
        """Update the preselected channels."""
        self._preselected_channels.update(new_preselected_channels)

    @property
    def trigger_event(self) -> tuple[int, int, str]:
        """Trigger event of this transition."""
        return self._trigger_event

    @trigger_event.setter
    def trigger_event(self, new_trigger_event: tuple[int, int, str]) -> None:
        self._trigger_event = new_trigger_event

    @property
    def name(self) -> str:
        """Name of this transition."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        self._name = new_name

    @property
    def frames(self) -> Sequence[SequenceKeyFrame]:
        """Get the frames of this transition."""
        return tuple(self._frames)

    def remove_frame(self, frame: SequenceKeyFrame) -> None:
        """Remove a frame from this transition."""
        self._frames.remove(frame)

    def format_for_filter(self) -> str:
        """Serialize this transition for filter format."""
        formatted_frame_list = [c.format_for_filter() for c in self._frames]
        return f"{self._trigger_event[0]}:{self._trigger_event[1]}#{self._name}#{'#'.join(formatted_frame_list)}"

    @staticmethod
    def from_filter_str(s: str, channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> Transition:
        """Deserialize this transition from filter format.

        Args:
            s: The serialized description.
            channels: The channel definition that this transition should be mapped to.

        """
        if isinstance(channels, list):
            new_dict = {}
            for c in channels:
                new_dict[c.name] = c
            channels = new_dict
        t = Transition()
        first_delim = s.find("#")
        event_def = s[:first_delim].split(":")
        t._trigger_event = (int(event_def[0]), int(event_def[1]), "")
        s = s[first_delim + 1 :]
        first_delim = s.find("#")
        t._name = s[:first_delim]
        s = s[first_delim + 1 :]
        for arg in s.split("#"):
            if len(arg) == 0:
                continue
            t._frames.append(SequenceKeyFrame.from_filter_str(arg, channels))
        return t

    def copy(self, new_channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> Transition:
        """Get a copy of this transition."""
        new_channels = _force_channel_dict(new_channels)
        t = Transition()
        t._trigger_event = self._trigger_event
        for skf in self._frames:
            t._frames.append(skf.copy(new_channels[skf.channel.name]))
        return t

    def to_cue(self) -> Cue:
        """Convert the transition to a cue object."""
        c = Cue()
        channels: dict[str, DataType] = dict(self.preselected_channels)
        for f in self._frames:
            channels[f.channel.name] = f.channel.data_type
        for k, v in channels.items():
            c.add_channel(k, v)
        channel_ages = Counter()
        for f in self._frames:
            ckf = KeyFrame(c)
            channel_name = f.channel.name
            ckf.only_on_channel = channel_name
            ckf.append_state(f.target_value_as_cue_state())
            channel_ages[channel_name] += f.duration
            ckf.timestamp = channel_ages[channel_name]
            c.insert_frame(ckf)
        return c

    def update_frames_from_cue(
        self, c: Cue, channel_dict: Sequence[SequencerChannel] | dict[str, SequencerChannel]
    ) -> None:
        """Update the content of this transition using a Cue object.

        Args:
            c: Cue to use as a reference
            channel_dict: Either a list of SequencerChannels or a dict of channel names and their SequencerChannels.

        """
        channel_dict = _force_channel_dict(channel_dict)
        self._frames.clear()
        c._frames.sort(key=lambda x: x.timestamp)
        channel_ages = Counter()
        for cf in c._frames:
            skf = SequenceKeyFrame(channel_dict.get(cf.only_on_channel))
            skf._target_value = cf._states[0]._value
            skf._tf = TransferFunction(cf._states[0].transition)
            skf._duration = cf.timestamp - channel_ages[cf.only_on_channel]
            channel_ages[cf.only_on_channel] += skf._duration
            self._frames.append(skf)

    @property
    def duration(self) -> float:
        """Get the duration of the transition in seconds."""
        if len(self._frames) == 0:
            return 0.0
        durations = Counter()
        for f in self._frames:
            durations[f._channel] += f._duration
        return max(durations.values())
