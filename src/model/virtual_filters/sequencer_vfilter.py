from typing import TYPE_CHECKING

from model import Scene
from model.filter import FilterTypeEnumeration
from model.virtual_filters.cue_vfilter import _PreviewFilter


class SequencerFilter(_PreviewFilter):
    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_SEQUENCER,
                         FilterTypeEnumeration.FILTER_SEQUENCER, pos=pos)
