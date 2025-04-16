from model import ColorHSI
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.transfer_function import TransferFunction


class SequenceKeyFrame:
    def __init__(self, target_channel: SequencerChannel):
        self.channel: SequencerChannel = target_channel
        self.target_value: int | float | ColorHSI = 0
        self.duration: float = 0.0
        self.tf: TransferFunction = TransferFunction.LINEAR

    def format_for_filter(self) -> str:
        value_str: str = self.target_value.format_for_filter() if isinstance(self.target_value, ColorHSI) else str(self.target_value)
        return f"{self.channel.name}:{value_str}:{self.tf.value}:{self.duration}"


class Transition:
    def __init__(self):
        self.frames: list[SequenceKeyFrame] = []

    def format_for_filter(self) -> str:
        return ";".join([c.format_for_filter() for c in self.frames])
