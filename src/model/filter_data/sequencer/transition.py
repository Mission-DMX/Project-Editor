from logging import getLogger

from model import ColorHSI, DataType
from model.filter_data.sequencer._utils import _rf
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.transfer_function import TransferFunction

logger = getLogger(__file__)


class SequenceKeyFrame:
    def __init__(self, target_channel: SequencerChannel):
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
        skf.duration = args[2]
        skf.tf = TransferFunction(args[3])
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


class Transition:
    def __init__(self):
        self._trigger_event = 0
        self.frames: list[SequenceKeyFrame] = []

    def format_for_filter(self) -> str:
        return f"{self._trigger_event}#{"#".join([c.format_for_filter() for c in self.frames])}"

    @staticmethod
    def from_filter_str(s: str, channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> "Transition":
        if isinstance(channels, list):
            new_dict = {}
            for c in channels:
                new_dict[c.name] = c
            channels = new_dict
        t = Transition()
        first_delim = s.find('#')
        t._trigger_event = int(s[:first_delim])  # TODO replace with EventSender, once #191 is merged.
        for arg in s.split("#")[first_delim+1:]:
            t.frames.append(SequenceKeyFrame.from_filter_str(arg, channels))
        return t

    def copy(self, new_channels: list[SequencerChannel] | dict[str, SequencerChannel]) -> "Transition":
        new_dict = {}
        for c in new_channels:
            new_dict[c.name] = c
        new_channels = new_dict
        t = Transition()
        t._trigger_event = self._trigger_event
        for skf in self.frames:
            t.frames.append(skf.copy(new_channels[skf.channel.name]))
        return t
