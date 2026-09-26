"""VFilter that provides pan, tilt and minimum brightness outputs for auto tracked moving heads."""

from model import Filter, Scene
from model.filter import DataType, FilterTypeEnumeration, VirtualFilter
from view.show_mode.show_ui_widgets.autotracker.v_filter_light_controller import VFilterLightController


class _MHControlInstance:
    def __init__(self, mh_id: int,
                 channel_data_type: DataType.DT_16_BIT | DataType.DT_8_BIT = DataType.DT_16_BIT) -> None:
        self.datatype: DataType.DT_16_BIT | DataType.DT_8_BIT = channel_data_type
        self.name_prefix: str = f"__MH_{mh_id}__"


class AutoTrackerFilter(VirtualFilter):
    """VFilter providing constant outputs for moving heads controlled by the auto tracker."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None) -> None:
        """Initialize the auto tracker filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_AUTOTRACKER, pos=pos)
        self._control_filters: dict[int, _MHControlInstance] = {}
        self._light_controller: VFilterLightController = VFilterLightController()
        self.out_data_types["minimum_brightness"] = DataType.DT_DOUBLE

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        """Resolve the virtual output port to the id of the constant filter providing it."""
        # TODO upgrade to multi tracker support
        match virtual_port_id:
            case "minimum_brightness":
                return self.get_min_brightness_filter_id()
            case "pan":
                return self.get_pan_filter_id(0)
            case "tilt":
                return self.get_tilt_filter_id(0)

    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        """Instantiate constant filters for the minimum brightness and all tracked moving heads."""
        # TODO implement multi tracker support
        filter_list.append(Filter(self.scene, self.get_min_brightness_filter_id(),
                                  FilterTypeEnumeration.FILTER_CONSTANT_FLOAT))
        for tf in self._control_filters.values():
            filter_list.append(Filter(self.scene, self.get_pan_filter_id(tf),
                                      FilterTypeEnumeration.FILTER_CONSTANT_8BIT if tf.datatype == DataType.DT_8_BIT
                                      else FilterTypeEnumeration.FILTER_CONSTANT_16_BIT))
            filter_list.append(Filter(self.scene, self.get_tilt_filter_id(tf),
                                      FilterTypeEnumeration.FILTER_CONSTANT_8BIT if tf.datatype == DataType.DT_8_BIT
                                      else FilterTypeEnumeration.FILTER_CONSTANT_16_BIT))

    def get_pan_filter_id(self, tracker_id: int | _MHControlInstance) -> str | None:
        """Get the id of the pan constant filter of the provided tracker."""
        if isinstance(tracker_id, int):
            mh_tracker = self._control_filters.get(tracker_id)
            if not mh_tracker:
                return None
        else:
            mh_tracker = tracker_id
        return f"{self.filter_id}{mh_tracker.name_prefix}PAN_Constant"

    def get_tilt_filter_id(self, tracker_id: int | _MHControlInstance) -> str | None:
        """Get the id of the tilt constant filter of the provided tracker."""
        if isinstance(tracker_id, int):
            mh_tracker = self._control_filters.get(tracker_id)
            if not mh_tracker:
                return None
        else:
            mh_tracker = tracker_id
        return f"{self.filter_id}{mh_tracker.name_prefix}TILT_Constant"

    def get_min_brightness_filter_id(self) -> str:
        """Get the id of the minimum brightness constant filter."""
        # TODO upgrade to multi tracker support
        return f"{self.filter_id}__min_brightness"

    def get_data_type_of_tracker(self, tracker_id: int | _MHControlInstance) -> DataType:
        """Get the channel data type used by the provided tracker."""
        if isinstance(tracker_id, _MHControlInstance):
            return tracker_id.datatype

        return self._control_filters[tracker_id].datatype

    @property
    def number_of_concurrent_trackers(self) -> int:
        """The number of moving heads tracked concurrently."""
        tr = self.filter_configurations.get("trackercount")
        if tr:
            try:
                tr = int(tr)
                if tr >= 0:
                    return tr
            except ValueError:
                pass
        self.filter_configurations["trackercount"] = "0"
        return 0

    @property
    def light_controller(self) -> VFilterLightController:
        """The light controller used to control the tracked moving heads."""
        return self._light_controller
