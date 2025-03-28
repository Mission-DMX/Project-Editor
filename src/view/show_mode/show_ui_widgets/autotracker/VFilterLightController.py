# coding=utf-8
from logging import getLogger
from typing import TYPE_CHECKING

from controller.autotrack.LightController import LightController

if TYPE_CHECKING:
    from model.virtual_filters import AutoTrackerFilter
    from view.show_mode.show_ui_widgets.autotracker.UIWidget import AutoTrackerUIWidget

logger = getLogger(__file__)


class VFilterLightController(LightController):
    """
    This class acts as a gateway between the remote detection thread and
    the change propagation of the constants generated by the v-filter.
    """

    def __init__(self, f: "AutoTrackerFilter"):
        super().__init__()
        self._minimum_brightness: float = 0.0
        self._widget: "AutoTrackerUIWidget" = None
        self.last_pan: int = 0
        self.last_tilt: int = 0

    def turn_on(self):
        self._minimum_brightness = 1.0
        self._request_update()

    def turn_off(self):
        self._minimum_brightness = 0.0
        self._request_update()

    def set_brightness(self, brightness: float):
        self._minimum_brightness = brightness
        self._request_update()

    def set_position(self, position: tuple[int, int]):
        self.last_pan = position[0]
        self.last_tilt = position[1]
        self._request_update()

    def set_color(self, color):
        logger.error(
            "Someone wanted to set the moving head color to '%s'. This however is not supported.", color)
        pass

    def _request_update(self):
        if not self._widget:
            logger.error("Unable to pass auto tracker updates. No UIWidget was loaded yet.")
            return
        self._widget.push_update()

    def set_ui_widget(self, w: "AutoTrackerUIWidget"):
        self._widget = w
