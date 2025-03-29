# coding=utf-8
from PySide6.QtCore import QTimer

from controller.joystick.joystick_enum import JoystickList
from model import Broadcaster, Scene
from model.filter import DataType, Filter, FilterTypeEnumeration, VirtualFilter


class PanTiltConstantFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, pos=pos)
        self._pan = 0.8
        self._tilt = 0.8
        self._filter_configurations = {}
        self._pan_delta = 0.0
        self._tilt_delta = 0.0
        self._joystick = JoystickList.NO_JOYSTICK
        self._broadcaster = Broadcaster()
        self._broadcaster.joystick_selected_event.connect(lambda joystick: self.set_joystick(
            JoystickList.NO_JOYSTICK if joystick == self._joystick else self._joystick))

        # Todo: maybe use timer in broadcaster
        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update_time_passed)
        self.observer = {}

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'pan8bit':
                return f"{self.filter_id}_8bit_pan:value_upper"
            case 'tilt8bit':
                return "{self.filter_id}_8bit_tilt:value_upper"
            case 'pan16bit':
                return "{self.filter_id}_16bit_pan:value"
            case 'tilt16bit':
                return "{self.filter_id}_16bit_tilt:value"
        return None

    def instantiate_filters(self, filter_list: list[Filter]):
        self.instantiate_16bit_constant_filter(filter_list, False)
        self.instantiate_16bit_constant_filter(filter_list, True)
        if self.eight_bit_available:
            self.instantiate_16bit_to_8bit_conversion_filter(filter_list, False)
            self.instantiate_16bit_to_8bit_conversion_filter(filter_list, True)

    def instantiate_16bit_constant_filter(self, filter_list: list[Filter], tilt: bool):
        filter = Filter(
            filter_id=f"{self.filter_id}_16bit_{'tilt' if tilt else 'pan'}",
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
            scene=self.scene
        )
        filter._initial_parameters = {
            'value': str(int((self.tilt if tilt else self.pan) * 65535))}  # Todo: inverse Tilt?
        filter._filter_configurations = {}
        filter._in_data_types = {}
        filter._out_data_types = {'value': DataType.DT_16_BIT}
        filter._gui_update_keys = {'value': DataType.DT_16_BIT}
        filter._in_data_types = {}
        filter._channel_links = {}
        filter_list.append(filter)

    def instantiate_16bit_to_8bit_conversion_filter(self, filter_list: list[Filter], tilt: bool):
        filter = Filter(
            filter_id=f"{self.filter_id}_8bit_{'tilt' if tilt else 'pan'}",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT,
            scene=self.scene
        )
        filter._initial_parameters = {}
        filter._filter_configurations = {}
        filter._in_data_types = {'value': DataType.DT_16_BIT}
        filter._out_data_types = {'value_lower': DataType.DT_8_BIT,
                                  'value_upper': DataType.DT_8_BIT}
        filter._gui_update_keys = {}
        filter._in_data_types = {}
        filter._channel_links = {'value': f"{self.filter_id}_16bit_{ 'tilt' if tilt else 'pan'}:value"}
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
    def pan_delta(self):
        return self._pan_delta

    @pan_delta.setter
    def pan_delta(self, pan_delta):
        self._pan_delta = pan_delta

    @property
    def tilt_delta(self):
        return self._tilt_delta

    @tilt_delta.setter
    def tilt_delta(self, tilt_delta):
        self._tilt_delta = tilt_delta

    def set_delta(self, delta: float, joystick: JoystickList, tilt: bool):
        if self._joystick != JoystickList.NO_JOYSTICK:
            if self._joystick in (joystick, JoystickList.EVERY_JOYSTICK):
                if tilt:
                    self._tilt_delta = delta
                else:
                    self._pan_delta = delta

    @property
    def sixteen_bit_available(self):
        return self._filter_configurations['outputs'] == 'both' or self._filter_configurations['outputs'] == '16bit'

    @property
    def eight_bit_available(self):
        return self._filter_configurations['outputs'] == 'both' or self._filter_configurations['outputs'] == '8bit'

    def update_time_passed(self):
        self._pan = min(max(self._pan + 0.01 * self._pan_delta, 0.0), 1.0)
        self._tilt = min(max(self._tilt + 0.01 * self._tilt_delta, 0.0), 1.0)
        self.notify_observer()

    def register_observer(self, obs, callback):
        self.observer[obs] = callback

    def notify_observer(self):
        for obs in self.observer:
            (self.observer[obs])()

    @property
    def joystick(self):
        return self._joystick

    @joystick.setter
    def joystick(self, joystick):
        if joystick != self._joystick:
            if joystick == JoystickList.NO_JOYSTICK:
                self._timer.stop()
            elif self._joystick == JoystickList.NO_JOYSTICK:
                self._timer.start()
                self._pan_delta = 0.0
                self._tilt_delta = 0.0
            self._broadcaster.joystick_selected_event.emit(joystick)
            self._joystick = joystick

    def set_joystick(self, joystick):
        self.joystick = joystick
