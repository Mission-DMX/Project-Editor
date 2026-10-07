"""Contains the sequencer v-filter model."""
from logging import getLogger
from typing import override

from model import Scene
from model.filter import DataType, FilterTypeEnumeration
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from model.virtual_filters.cue_vfilter import PreviewFilter

logger = getLogger(__name__)


class SequencerFilter(PreviewFilter):
    """Sequencer v-filter."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None) -> None:
        """Initialize v-filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_SEQUENCER,
                         FilterTypeEnumeration.FILTER_SEQUENCER, pos=pos)

    @override
    def _rebuild_io(self) -> None:
        """Reset I/O and derive outputs from ``filter_configurations["channels"]``.

        Called at construction (empty configs) and again by the loader after XML population,
        so a loaded sequencer filter has its typed outputs populated before the editor view
        opens. Malformed channel entries are logged and skipped so corrupt show files still
        load.
        """
        self._in_data_types = {"time": DataType.DT_DOUBLE, "time_scale": DataType.DT_DOUBLE}
        self._out_data_types = {}
        self._default_values = {"time_scale": "1.0"}
        self._gui_update_keys = {}
        self._filter_configurations.setdefault("channels", "")
        self._filter_configurations.setdefault("transitions", "")
        for c_str in self._filter_configurations.get("channels", "").split(";"):
            if not c_str:
                continue
            try:
                channel = SequencerChannel.from_filter_str(c_str)
            except (ValueError, IndexError):
                logger.warning(
                    "SequencerFilter %s: malformed channel entry %r, skipping", self._filter_id, c_str
                )
                continue
            self._out_data_types[channel.name] = channel.data_type
