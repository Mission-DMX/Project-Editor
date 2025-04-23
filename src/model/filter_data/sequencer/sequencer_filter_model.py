from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.sequencer.transition import Transition


class SequencerFilterModel:
    def __init__(self):
        self.channels: list[SequencerChannel] = []
        self.transitions: list[Transition] = []

    def load_configuration(self, d: dict[str, str]):
        self.channels.clear()
        for c_str in d["channels"].split(';'):
            if len(c_str) == 0:
                continue
            c = SequencerChannel.from_filter_str(c_str)
            self.channels.append(c)
        self.transitions.clear()
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

    def remove_channels(self, selected_items: list[str] | list[SequencerChannel]):
        for c in selected_items:
            if isinstance(c, SequencerChannel):
                c_name = c.name
                self.channels.remove(c)
            else:
                c_name = c
                to_remove = []
                for rc in self.channels:
                    if rc.name == c_name:
                        to_remove.append(rc)
                for rc in to_remove:
                    self.channels.remove(rc)
            for t in self.transitions:
                to_remove = []
                for skf in t.frames:
                    if skf.channel.name == c_name:
                        to_remove.append(skf)
                for rc in to_remove:
                    t.frames.remove(rc)

    def get_channel_by_name(self, c_name: str) -> SequencerChannel | None:
        for c in self.channels:
            if c.name == c_name:
                return c
        return None

    def append_channel(self, c: SequencerChannel):
        self.channels.append(c)
