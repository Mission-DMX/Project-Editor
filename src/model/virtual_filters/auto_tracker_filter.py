# coding=utf-8
from model import Filter, Scene
from model.filter import DataType, FilterTypeEnumeration, VirtualFilter
from view.show_mode.show_ui_widgets.autotracker.VFilterLightController import VFilterLightController


class _MHControlInstance:
    def __init__(self, mh_id: int, channel_data_type: DataType.DT_16_BIT | DataType.DT_8_BIT = DataType.DT_16_BIT):
        self.datatype: DataType.DT_16_BIT | DataType.DT_8_BIT = channel_data_type
        self.name_prefix: str = f"__MH_{mh_id}__"


class AutoTrackerFilter(VirtualFilter):

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_AUTOTRACKER, pos=pos)
        self._control_filters: dict[int, _MHControlInstance] = {}
        self._light_controller: VFilterLightController = VFilterLightController(self)
        self.out_data_types["minimum_brightness"] = DataType.DT_DOUBLE

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        # TODO upgrade to multi tracker support
        match virtual_port_id:
            case "minimum_brightness":
                return self.get_min_brightness_filter_id(0)
            case "pan":
                return self.get_pan_filter_id(0)
            case "tilt":
                return self.get_tilt_filter_id(0)

    def instantiate_filters(self, filter_list: list[Filter]):
        # TODO implement multi tracker support
        filter_list.append(Filter(self.scene, self.get_min_brightness_filter_id(0),
                                  FilterTypeEnumeration.FILTER_CONSTANT_FLOAT))
        for tf in self._control_filters.values():
            filter_list.append(Filter(self.scene, self.get_pan_filter_id(tf),
                                      FilterTypeEnumeration.FILTER_CONSTANT_8BIT if tf.datatype == DataType.DT_8_BIT
                                      else FilterTypeEnumeration.FILTER_CONSTANT_16_BIT))
            filter_list.append(Filter(self.scene, self.get_tilt_filter_id(tf),
                                      FilterTypeEnumeration.FILTER_CONSTANT_8BIT if tf.datatype == DataType.DT_8_BIT
                                      else FilterTypeEnumeration.FILTER_CONSTANT_16_BIT))

    def get_pan_filter_id(self, tracker_id: int | _MHControlInstance) -> str | None:
        if isinstance(tracker_id, int):
            mh_tracker = self._control_filters.get(tracker_id)
            if not mh_tracker:
                return None
        else:
            mh_tracker = tracker_id
        return f"{self.filter_id}{mh_tracker.name_prefix}PAN_Constant"

    def get_tilt_filter_id(self, tracker_id: int | _MHControlInstance) -> str | None:
        if isinstance(tracker_id, int):
            mh_tracker = self._control_filters.get(tracker_id)
            if not mh_tracker:
                return None
        else:
            mh_tracker = tracker_id
        return f"{self.filter_id}{mh_tracker.name_prefix}TILT_Constant"

    def get_min_brightness_filter_id(self, tracker_id: int | _MHControlInstance):
        # TODO upgrade to multi tracker support
        return f"{self.filter_id}__min_brightness"

    def get_data_type_of_tracker(self, tracker_id: int | _MHControlInstance) -> DataType:
        if isinstance(tracker_id, _MHControlInstance):
            return tracker_id.datatype

        return self._control_filters[tracker_id].datatype

    @property
    def number_of_concurrent_trackers(self) -> int:
        tr = self.filter_configurations.get("trackercount")
        if tr:
            try:
                tr = int(tr)
                if tr >= 0:
                    return tr
            except ValueError:
                pass
        self.filter_configurations['trackercount'] = '0'
        return 0

    @property
    def light_controller(self) -> VFilterLightController:
        return self._light_controller
