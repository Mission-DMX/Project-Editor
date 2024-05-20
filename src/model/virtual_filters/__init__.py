from model import Scene
from model.filter import Filter, VirtualFilter, FilterTypeEnumeration
from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from model.virtual_filters.cue_vfilter import CueFilter
from model.virtual_filters.range_adapters import SixteenBitToFloatRange, EightBitToFloatRange


def construct_virtual_filter_instance(scene: Scene, filter_type: int, filter_id: str, pos: tuple[int] | None = None) -> VirtualFilter:
    if not filter_type < 0:
        raise ValueError("The provided filter is not a virtual description.")
    match filter_type:
        case FilterTypeEnumeration.VFILTER_COMBINED_FILTER_PRESET:
            # TODO return virtual filter that instantiates a preset (as described in issue #48)
            pass
        case FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            return PanTiltConstantFilter(scene, filter_id, pos=pos)

        case FilterTypeEnumeration.VFILTER_CUES:
            return CueFilter(scene, filter_id, pos=pos)
            pass
        case FilterTypeEnumeration.VFILTER_EFFECTSSTACK:
            # TODO implement effects stack virtual filter (as described in issue #87)
            pass
        case FilterTypeEnumeration.VFILTER_AUTOTRACKER:
            return AutoTrackerFilter(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_UNIVERSE:
            # TODO implement a virtual filter that accepts a patching fixture as configuration making sure that one can
            # edit the patching and does not have to edit all universe filters by hand. Filling in defaults for channels
            # should also be possible causing the v-filter to instantiate constants.
            pass
        case FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE:
            return SixteenBitToFloatRange(scene, filter_id, pos=pos)
        case FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE:
            return EightBitToFloatRange(scene, filter_id, pos=pos)
        case _:
            raise ValueError("The requested filter type {} is not yet implemented.".format(filter_type))
    pass
