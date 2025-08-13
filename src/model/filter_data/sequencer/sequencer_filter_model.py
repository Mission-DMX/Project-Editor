"""Contains the sequencer filter model."""

from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.filter_data.sequencer.transition import Transition


class SequencerFilterModel:
    """Model of a sequencer filter."""

    def __init__(self) -> None:
        """Initialize the model."""
        self.channels: list[SequencerChannel] = []
        self.transitions: list[Transition] = []

    def load_configuration(self, d: dict[str, str]) -> None:
        """Load the configuration of this filter."""
        self.channels.clear()
        for c_str in d["channels"].split(";"):
            if len(c_str) == 0:
                continue
            c = SequencerChannel.from_filter_str(c_str)
            self.channels.append(c)
        self.transitions.clear()
        for t_str in d["transitions"].split(";"):
            if len(t_str) == 0:
                continue
            t = Transition.from_filter_str(t_str, self.channels)
            self.transitions.append(t)

    def get_configuration(self) -> dict[str, str]:
        """Get the configuration of this filter."""
        return {
            "channels": ";".join([c.format_for_filter() for c in self.channels]),
            "transitions": ";".join([t.format_for_filter() for t in self.transitions])
        }

    def remove_channels(self, selected_items: list[str] | list[SequencerChannel]) -> None:
        """Remove provided channels from model."""
        for c in selected_items:
            if isinstance(c, SequencerChannel):
                c_name = c.name
                self.channels.remove(c)
            else:
                c_name = c
                to_remove = [rc for rc in self.channels if rc.name == c_name]
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
        """Lookup a channel by its name.

        Note: At the moment, this operation is slow as there is no index. However, as n is usually small, fixing this
        isn't a high priority.

        :param c_name: Name of the channel to look up.
        :return: The channel corresponding to the given name or None if not found.
        """
        for c in self.channels:
            if c.name == c_name:
                return c
        return None

    def append_channel(self, c: SequencerChannel) -> None:
        """Add a channel to the model."""
        if self.get_channel_by_name(c.name) is not None:
            return
        self.channels.append(c)
