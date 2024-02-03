from PySide6.QtCore import QTimer

from model import Scene
from model.filter import VirtualFilter, Filter, DataType, FilterTypeEnumeration


class PanTiltConstantFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, pos=pos)
        self._pan = 0.8
        self._tilt = 0.8
        self._filter_configurations = {}
        self._update_allowed = False
        self._pan_delta = 0.0
        self._tilt_delta = 0.0


        # Todo: maybe use timer in broadcaster
        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update_time_passed)
        self.observer = {}

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'pan_8bit':
                return "{}_8bit_pan.value_upper".format(self.filter_id)
            case 'tilt_8bit':
                return "{}_8bit_tilt.value_upper".format(self.filter_id)
            case 'pan_16bit':
                return "{}_16bit_pan.value".format(self.filter_id)
            case 'tilt_16bit':
                return "{}_16bit_tilt.value".format(self.filter_id)
        return "error"

    def instantiate_filters(self, filter_list: list[Filter]):
        self.instanitate_16bit_constant_filter(filter_list, False)
        self.instanitate_16bit_constant_filter(filter_list, True)
        if self.eight_bit_available:
            self.instanitate_16bit_to_8bit_conversion_filter(filter_list, False)
            self.instanitate_16bit_to_8bit_conversion_filter(filter_list, True)

    def instanitate_16bit_constant_filter(self, filter_list: list[Filter], tilt: bool):
        filter = Filter(
            filter_id="{}_16bit_{}".format(self.filter_id, 'tilt' if tilt else 'pan'),
            filter_type=1,
            scene=self.scene
        )
        filter._initial_parameters = {'value': str(int(self.tilt * 65535))}
        filter._filter_configurations = {}
        filter._in_data_types = {}
        filter._out_data_types = {'value': DataType.DT_16_BIT}
        filter._gui_update_keys = {'value': DataType.DT_16_BIT}
        filter._in_data_types = {}
        filter._channel_links = {}
        filter_list.append(filter)

    def instanitate_16bit_to_8bit_conversion_filter(self, filter_list: list[Filter], tilt: bool):
        filter = Filter(
            filter_id="{}_8bit_{}".format(self.filter_id,
                                          'tilt' if tilt else 'pan'),
            filter_type=8,
            scene=self.scene
        )
        filter._initial_parameters = {}
        filter._filter_configurations = {}
        filter._in_data_types = {'value': DataType.DT_16_BIT}
        filter._out_data_types = {'value_lower': DataType.DT_8_BIT,
                                  'value_upper': DataType.DT_8_BIT}
        filter._gui_update_keys = {}
        filter._in_data_types = {}
        filter._channel_links = {'value': "{}_16bit_{}.value".format(self.filter_id, 'tilt' if tilt else 'pan')}
        filter_list.append(filter)

    @property
    def pan(self):
        return self._pan

    @pan.setter
    def pan(self, pan):
        self._pan = pan
        self.notify_observer()

    @property
    def tilt(self):
        return self._tilt

    @tilt.setter
    def tilt(self, tilt):
        self._tilt = tilt
        self.notify_observer()

    @property
    def update_allowed(self):
        return self._update_allowed

    @update_allowed.setter
    def update_allowed(self, update_allowed):
        if update_allowed:
            self._timer.start()
        else:
            self._timer.stop()
        self._update_allowed = update_allowed

    @property
    def pan_delta(self):
        return self._pan_delta

    @pan_delta.setter
    def pan_delta(self, pan_delta):
        if self._update_allowed:
            self._pan_delta = pan_delta

    @property
    def tilt_delta(self):
        return self._tilt_delta

    @tilt_delta.setter
    def tilt_delta(self, tilt_delta):
        if self._update_allowed:
            self._tilt_delta = tilt_delta

    @property
    def sixteen_bit_available(self):
        return self._filter_configurations['outputs'] == 'both' or self._filter_configurations['outputs'] == '16bit'

    @property
    def eight_bit_available(self):
        return self._filter_configurations['outputs'] == 'both' or self._filter_configurations['outputs'] == '8bit'

    def update_time_passed(self):
        if self._update_allowed:
            self._pan = min(max(self._pan + 0.01 * self._pan_delta, 0.0), 1)
            self._tilt = min(max(self._tilt + 0.01 * self._tilt_delta, 0.0), 1)
            self.notify_observer()

    def register_observer(self, obs, callback):
        self.observer[obs] = callback

    def notify_observer(self):
        for obs in self.observer:
            (self.observer[obs])()
