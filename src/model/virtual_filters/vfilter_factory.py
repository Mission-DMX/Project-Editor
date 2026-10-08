"""V-Filter factory.

Internal module used exclusively by :func:`model.filters.factory.construct_filter_instance`
to construct :class:`~model.filter.VirtualFilter` subclasses. External callers should go
through the unified :func:`construct_filter_instance` entry point rather than importing
from here directly — v-filter classes aren't registered in the type → subclass map today
(their constructors use the pre-migration ``(scene, filter_id, pos)`` signature), so this
module provides the dispatch instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter import FilterTypeEnumeration
from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
from model.virtual_filters.color_mixer_vfilter import ColorMixerVFilter
from model.virtual_filters.color_to_colorwheel import ColorToColorWheel
from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter
from model.virtual_filters.cue_vfilter import CueFilter
from model.virtual_filters.effects_stacks.vfilter import EffectsStack
from model.virtual_filters.import_vfilter import ImportVFilter
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from model.virtual_filters.range_adapters import (
    ColorGlobalBrightnessMixinVFilter,
    DimmerGlobalBrightnessMixinVFilter,
    EightBitToFloatRange,
    SixteenBitToFloatRange,
)
from model.virtual_filters.sequencer_vfilter import SequencerFilter

if TYPE_CHECKING:
    from model import Scene
    from model.filter import VirtualFilter


def _construct_virtual_filter_instance_legacy(
    scene: Scene, filter_type: int, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None
) -> VirtualFilter | None:
    """Original match-based v-filter construction.

    Used by :func:`model.filters.factory.construct_filter_instance` as the fallback for
    v-filter type codes that do not yet have a subclass registered under
    :mod:`model.filters.virtual`. Once every v-filter has been migrated this function and
    its public shim can be deleted.
    """
    if not filter_type < 0:
        raise ValueError("The provided filter is not a virtual description.")
    match filter_type:
        case FilterTypeEnumeration.VFILTER_COMBINED_FILTER_PRESET:
            # TODO return virtual filter that instantiates a preset (as described in issue #48)
            return None
        case FilterTypeEnumeration.VFILTER_COLORDIRECTOR:
            return ColordirectorVFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            return PanTiltConstantFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN:
            return DimmerGlobalBrightnessMixinVFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_CUES:
            return CueFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_EFFECTSSTACK:
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
        case FilterTypeEnumeration.VFILTER_COLOR_TO_COLORWHEEL:
            return ColorToColorWheel(scene, filter_id, pos=pos)
        case _:
            raise ValueError(f"The requested filter type {filter_type} is not yet implemented.")
