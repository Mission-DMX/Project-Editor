from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.sequencer.transition import Transition


class SequencerFilterModel:
    def __init__(self):
        self.channels: list[SequencerChannel] = []
        self.transitions: list[Transition] = []

    def load_configuration(self, d: dict[str, str]):
        self.channels.clear()
        for c_str in d["channels"].split(';'):
            c = SequencerChannel.from_filter_str(c_str)
            self.channels.append(c)
        for t_str in d["transitions"].split(';'):
            if len(t_str) == 0:
                continue
            t = Transition.from_filter_str(t_str, self.channels)
            self.transitions.append(t)

    def get_configuration(self):
        return {
            "channels": ';'.join([c.format_for_filter() for c in self.channels]),
            "transitions": ';'.join([t.format_for_filter() for t in self.transitions])
        }
