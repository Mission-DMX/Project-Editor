"""V-Filter factory.

This file provides a factory for v-filter instances. The primary use case is for restoring efforts after loading a
show file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter import FilterTypeEnumeration
from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
from model.virtual_filters.color_mixer_vfilter import ColorMixerVFilter
from model.virtual_filters.cue_vfilter import CueFilter
from model.virtual_filters.effects_stacks.vfilter import EffectsStack
from model.virtual_filters.fader_vfilter import FaderUpdatingVFilter
from model.virtual_filters.import_vfilter import ImportVFilter
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from model.virtual_filters.range_adapters import (
    ColorGlobalBrightnessMixinVFilter,
    EightBitToFloatRange,
    SixteenBitToFloatRange,
)
from model.virtual_filters.sequencer_vfilter import SequencerFilter

if TYPE_CHECKING:
    from model import Scene
    from model.filter import VirtualFilter


def construct_virtual_filter_instance(
    scene: Scene, filter_type: int, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None
) -> VirtualFilter | None:
    """Construct virtual filters.

    This method constructs instances of v-filter based on the provided model for the restoring of show files.

    Args:
        scene: The parent scene of the filter to be constructed.
        filter_type: The type of filter to instantiate
        filter_id: The id of the filter to instantiate
        pos: The position inside the editor of the filter to instantiate.

    Returns: The generated v-filter

    """
    if not filter_type < 0:
        raise ValueError("The provided filter is not a virtual description.")
    match filter_type:
        case (FilterTypeEnumeration.VFILTER_FADER_RAW | FilterTypeEnumeration.VFILTER_FADER_HSI |
        FilterTypeEnumeration.VFILTER_FADER_HSIA | FilterTypeEnumeration.FILTER_FADER_HSIU |
        FilterTypeEnumeration.FILTER_FADER_HSIAU):
            return FaderUpdatingVFilter(scene, filter_id, filter_type, pos=pos)
        case FilterTypeEnumeration.VFILTER_COMBINED_FILTER_PRESET:
            # TODO return virtual filter that instantiates a preset (as described in issue #48)
            return None
        case FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            return PanTiltConstantFilter(scene, filter_id, pos=pos)

        case FilterTypeEnumeration.VFILTER_CUES:
            return CueFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_EFFECTSSTACK:
            # TODO implement effects stack virtual filter (as described in issue #87)
            return EffectsStack(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_AUTOTRACKER:
            return AutoTrackerFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_UNIVERSE:
            # TODO implement a virtual filter that accepts a patching fixture as configuration making sure that one can
            # edit the patching and does not have to edit all universe filters by hand. Filling in defaults for channels
            # should also be possible causing the v-filter to instantiate constants.
            return None
        case FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE:
            return SixteenBitToFloatRange(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE:
            return EightBitToFloatRange(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN:
            return ColorGlobalBrightnessMixinVFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_IMPORT:
            return ImportVFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_COLOR_MIXER:
            return ColorMixerVFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_SEQUENCER:
            return SequencerFilter(scene, filter_id, pos=pos)
        case _:
            raise ValueError(f"The requested filter type {filter_type} is not yet implemented.")
