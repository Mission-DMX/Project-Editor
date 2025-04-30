from collections import Counter
from logging import getLogger

from model import ColorHSI, DataType
from model.filter_data.cues.cue import Cue, KeyFrame, State, StateColor, StateDouble, StateEightBit, StateSixteenBit
from model.filter_data.sequencer._utils import _rf
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.transfer_function import TransferFunction

logger = getLogger(__file__)


class SequenceKeyFrame:
    def __init__(self, target_channel: SequencerChannel):
        if target_channel is None:
            logger.error('target_channel is None')
        self.channel: SequencerChannel = target_channel
        self.target_value: int | float | ColorHSI = 0
        self.duration: float = 0.0
        self.tf: TransferFunction = TransferFunction.LINEAR

    def format_for_filter(self) -> str:
        value_str: str = self.target_value.format_for_filter() if isinstance(self.target_value, ColorHSI) else str(self.target_value)
        return f"{_rf(self.channel.name)}:{value_str}:{self.tf.value}:{self.duration}"

    @staticmethod
    def from_filter_str(s: str, channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> "SequenceKeyFrame":
        args = s.split(':')
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
                skf.target_value = max(0, min(255, int(args[1])))
            case DataType.DT_16_BIT:
                skf.target_value = max(0, min(65535, int(args[1])))
            case DataType.DT_DOUBLE:
                skf.target_value = float(args[1])
            case DataType.DT_BOOL:
                skf.target_value = max(0, min(1, int(args[1])))
            case DataType.DT_COLOR:
                skf.target_value = ColorHSI.from_filter_str(args[1])
            case _:
                logger.error("Execpected data type: {}", found_channel.data_type)
        skf.duration = float(args[3])
        skf.tf = TransferFunction(args[2])
        return skf

    def copy(self, new_target: SequencerChannel) -> "SequenceKeyFrame":
        if self.channel.name != new_target.name or self.channel == new_target:
            logger.warning("Expected copy of own channel for generation.")
        sc = SequenceKeyFrame(new_target)
        if self.channel.data_type == DataType.DT_COLOR:
            sc.target_value = self.target_value.copy()
        else:
            sc.target_value = self.target_value
        sc.duration = self.duration
        sc.tf = self.tf
        return sc

    def target_value_as_cue_state(self) -> State:
        match self.channel.data_type:
            case DataType.DT_8_BIT:
                s = StateEightBit(self.tf.value)
            case DataType.DT_16_BIT:
                s = StateSixteenBit(self.tf.value)
            case DataType.DT_DOUBLE:
                s = StateDouble(self.tf.value)
            case DataType.DT_COLOR:
                s = StateColor(self.tf.value)
            case DataType.DT_BOOL:
                s = StateEightBit(self.tf.value)
        s._value = self.target_value
        return s


def _force_channel_dict(cd: list[SequencerChannel] | dict[str, SequencerChannel]) -> dict[str, SequencerChannel]:
    if isinstance(cd, dict):
        return cd
    new_dict = {}
    for c in cd:
        new_dict[c.name] = c
    return new_dict


class Transition:
    def __init__(self):
        self._trigger_event: tuple[int, int, str] = (0, 0, "")
        self.frames: list[SequenceKeyFrame] = []
        self.name: str = ""
        self.preselected_channels: dict[str, DataType] = {}

    def format_for_filter(self) -> str:
        return f"{self._trigger_event[0]}:{self._trigger_event[1]}#{self.name}#{"#".join([c.format_for_filter() for c in self.frames])}"

    @staticmethod
    def from_filter_str(s: str, channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> "Transition":
        if isinstance(channels, list):
            new_dict = {}
            for c in channels:
                new_dict[c.name] = c
            channels = new_dict
        t = Transition()
        first_delim = s.find('#')
        event_def = s[:first_delim].split(':')
        t._trigger_event = (int(event_def[0]), int(event_def[1]), "")
        s = s[first_delim+1:]
        first_delim = s.find('#')
        t.name = s[:first_delim]
        s = s[first_delim + 1:]
        for arg in s.split("#"):
            t.frames.append(SequenceKeyFrame.from_filter_str(arg, channels))
        return t

    def copy(self, new_channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> "Transition":
        new_channels = _force_channel_dict(new_channels)
        t = Transition()
        t._trigger_event = self._trigger_event
        for skf in self.frames:
            t.frames.append(skf.copy(new_channels[skf.channel.name]))
        return t

    def to_cue(self) -> Cue:
        c = Cue()
        channels: dict[str, DataType] = {}
        for c_name, dtype in self.preselected_channels.items():
            channels[c_name] = dtype
        for f in self.frames:
            channels[f.channel.name] = f.channel.data_type
        for k, v in channels.items():
            c.add_channel(k, v)
        channel_ages = Counter()
        for f in self.frames:
            ckf = KeyFrame(c)
            channel_name = f.channel.name
            ckf.only_on_channel = channel_name
            ckf.append_state(f.target_value_as_cue_state())
            channel_ages[channel_name] += f.duration
            ckf.timestamp = channel_ages[channel_name]
            c.insert_frame(ckf)
        return c

    def update_frames_from_cue(self, c: Cue, channel_dict: list[SequencerChannel] | dict[str, SequencerChannel]):
        channel_dict = _force_channel_dict(channel_dict)
        self.frames.clear()
        c._frames.sort(key=lambda x: x.timestamp)
        channel_ages = Counter()
        for cf in c._frames:
            skf = SequenceKeyFrame(channel_dict.get(cf.only_on_channel))
            skf.target_value = cf._states[0]._value
            skf.tf = TransferFunction(cf._states[0].transition)
            skf.duration = cf.timestamp - channel_ages[cf.only_on_channel]
            channel_ages[cf.only_on_channel] += skf.duration
            self.frames.append(skf)

    @property
    def duration(self) -> float:
        if len(self.frames) == 0:
            return 0.0
        durations = Counter()
        for f in self.frames:
            durations[f.channel] += f.duration
        return max(durations.values())
