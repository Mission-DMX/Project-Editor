"""Virtual filter providing combined constants for pan and tilt."""
from __future__ import annotations

import typing

from PySide6.QtCore import QTimer

from controller.joystick.joystick_enum import JoystickList
from model import Broadcaster, Scene
from model.filter import DataType, Filter, FilterTypeEnumeration, VirtualFilter

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    from view.show_mode.show_ui_widgets import PanTiltConstantControlUIWidget


class PanTiltConstantFilter(VirtualFilter):
    """Virtual filter providing combined constants for pan and tilt."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Initializes the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, pos=pos)
        self._pan: float = 0.8
        self._tilt: float = 0.8
        self._filter_configurations: dict[str, str] = {}
        self._pan_delta: float = 0.0
        self._tilt_delta: float = 0.0
        self._joystick = JoystickList.NO_JOYSTICK
        self._broadcaster = Broadcaster()
        self._broadcaster.joystick_selected_event.connect(lambda joystick: self.set_joystick(
            JoystickList.NO_JOYSTICK if joystick == self._joystick else self._joystick))

        # Todo: maybe use timer in broadcaster
        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._update_time_passed)
        self.observer: dict[PanTiltConstantControlUIWidget, Callable[[], None]] = {}

    @typing.override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case "pan8bit":
                return f"{self.filter_id}_8bit_pan:value_upper"
            case "tilt8bit":
                return f"{self.filter_id}_8bit_tilt:value_upper"
            case "pan16bit":
                return f"{self.filter_id}_16bit_pan:value"
            case "tilt16bit":
                return f"{self.filter_id}_16bit_tilt:value"
        return None

    @typing.override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        self._instantiate_16bit_constant_filter(filter_list, False)
        self._instantiate_16bit_constant_filter(filter_list, True)
        if self.eight_bit_available:
            self._instantiate_16bit_to_8bit_conversion_filter(filter_list, False)
            self._instantiate_16bit_to_8bit_conversion_filter(filter_list, True)

    def _instantiate_16bit_constant_filter(self, filter_list: list[Filter], tilt: bool) -> None:
        filter_ = Filter(
            filter_id=f"{self.filter_id}_16bit_{'tilt' if tilt else 'pan'}",
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
            scene=self.scene,
        )
        filter_._initial_parameters = {
            "value": str(int((self.tilt if tilt else self.pan) * 65535))}  # Todo: inverse Tilt?
        filter_._filter_configurations = {}
        filter_._in_data_types = {}
        filter_._out_data_types = {"value": DataType.DT_16_BIT}
        filter_._gui_update_keys = {"value": DataType.DT_16_BIT}
        filter_._in_data_types = {}
        filter_._channel_links = {}
        filter_list.append(filter_)

    def _instantiate_16bit_to_8bit_conversion_filter(self, filter_list: list[Filter], tilt: bool) -> None:
        filter_ = Filter(
            filter_id=f"{self.filter_id}_8bit_{'tilt' if tilt else 'pan'}",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT,
            scene=self.scene,
        )
        filter_._initial_parameters = {}
        filter_._filter_configurations = {}
        filter_._in_data_types = {"value": DataType.DT_16_BIT}
        filter_._out_data_types = {"value_lower": DataType.DT_8_BIT,
                                   "value_upper": DataType.DT_8_BIT}
        filter_._gui_update_keys = {}
        filter_._in_data_types = {}
        filter_._channel_links = {"value": f"{self.filter_id}_16bit_{'tilt' if tilt else 'pan'}:value"}
        filter_list.append(filter_)

    @property
    def pan(self) -> float:
        """Get or set the pan constant."""
        return self._pan

    @pan.setter
    def pan(self, pan: float) -> None:
        self._pan = pan
        self._notify_observer()

    @property
    def tilt(self) -> float:
        """Get or set the tilt constant."""
        return self._tilt

    @tilt.setter
    def tilt(self, tilt: float) -> None:
        self._tilt = tilt
        self._notify_observer()

    @property
    def pan_delta(self) -> float:
        """Get or set the pan delta.

        The pan delta is the change applied per input movement. A larger delta results in faster changes.

        """
        return self._pan_delta

    @pan_delta.setter
    def pan_delta(self, pan_delta: float) -> None:
        self._pan_delta = pan_delta

    @property
    def tilt_delta(self) -> float:
        """Get or set the tilt delta.

        The tilt delta is the change applied per input movement. A larger delta results in faster changes.

        """
        return self._tilt_delta

    @tilt_delta.setter
    def tilt_delta(self, tilt_delta: float) -> None:
        self._tilt_delta = tilt_delta

    def set_delta(self, delta: float, joystick: JoystickList, tilt: bool) -> None:
        """Use this method to input joystick movements."""
        if self._joystick != JoystickList.NO_JOYSTICK and self._joystick in (joystick, JoystickList.EVERY_JOYSTICK):
            if tilt:
                self._tilt_delta = delta
            else:
                self._pan_delta = delta

    @property
    def sixteen_bit_available(self) -> bool:
        """Check if the filter configured to use sixteen bits."""
        return self._filter_configurations["outputs"] == "both" or self._filter_configurations["outputs"] == "16bit"

    @property
    def eight_bit_available(self) -> bool:
        """Check if the filter configured to use eight bits."""
        return self._filter_configurations["outputs"] == "both" or self._filter_configurations["outputs"] == "8bit"

    def _update_time_passed(self) -> None:
        self._pan = min(max(self._pan + 0.01 * self._pan_delta, 0.0), 1.0)
        self._tilt = min(max(self._tilt + 0.01 * self._tilt_delta, 0.0), 1.0)
        self._notify_observer()

    def register_observer(self, obs: PanTiltConstantControlUIWidget, callback: Callable[[], None]) -> None:
        """Register a callback to be notified upon value change."""
        self.observer[obs] = callback

    def _notify_observer(self) -> None:
        for obs in self.observer:
            (self.observer[obs])()

    @property
    def joystick(self) -> JoystickList:
        """Get or set the joystick associated with this input."""
        return self._joystick

    @joystick.setter
    def joystick(self, joystick: JoystickList) -> None:
        if joystick != self._joystick:
            if joystick == JoystickList.NO_JOYSTICK:
                self._timer.stop()
            elif self._joystick == JoystickList.NO_JOYSTICK:
                self._timer.start()
                self._pan_delta = 0.0
                self._tilt_delta = 0.0
            self._broadcaster.joystick_selected_event.emit(joystick)
            self._joystick = joystick

    def set_joystick(self, joystick: JoystickList) -> None:
        """Update a specific joystick."""
        self.joystick = joystick
