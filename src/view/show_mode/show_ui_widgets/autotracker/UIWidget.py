from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QDialog, QWidget

from model import UIPage, UIWidget
from view.show_mode.show_ui_widgets.autotracker.AutoTrackDialogWidget import AutoTrackDialogWidget
from view.show_mode.show_ui_widgets.autotracker.VFilterLightController import VFilterLightController

if TYPE_CHECKING:
    from model import Filter

logger = getLogger(__file__)


class AutoTrackerUIWidget(UIWidget):

    def __init__(self, parent_page: "UIPage", configuration: dict[str, str] = None):
        super().__init__(parent_page, configuration)
        self._finished_initializing: bool = False

    def set_filter(self, associated_filter: "Filter", i: int):
        super().set_filter(associated_filter, i)
        if not associated_filter:
            return
        from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
        if associated_filter:
            if not isinstance(associated_filter, AutoTrackerFilter):
                raise ValueError("Expected AutoTrackerFilter.")
        else:
            raise ValueError("The provided filter id does not exist.")
        self._associated_filter: AutoTrackerFilter = associated_filter
        self._tracker_player_widget = AutoTrackDialogWidget(associated_filter)
        self._tracker_player_widget.instance.settings.lights.set_ui_widget(self)
        # self._tracker_configuration_widget = SettingsTab("", self._tracker_player_widget.instance)
        self._tracker_configuration_widget = AutoTrackDialogWidget(associated_filter,
                                                                   self._tracker_player_widget.instance)
        self._finished_initializing = True

    def generate_update_content(self) -> list[tuple[str, str]]:
        filter_updates = []
        if not self._finished_initializing:
            return filter_updates
        lc = self._tracker_player_widget.instance.settings.lights
        # TODO handle case of VFILTER_POSITION_CONSTANT
        if not isinstance(lc, VFilterLightController):
            logger.error("Expected VFilterLightController. Got %s instead.", type(lc))
        for tracker_id in range(self._associated_filter.number_of_concurrent_trackers):
            pan_filter_id = self._associated_filter.get_pan_filter_id(tracker_id)
            tilt_filter_id = self._associated_filter.get_tilt_filter_id(tracker_id)
            if not pan_filter_id or not tilt_filter_id:
                continue
            # TODO upgrade value query to multi tracker support
            filter_updates.append((pan_filter_id, str(lc.last_pan)))
            filter_updates.append((tilt_filter_id, str(lc.last_tilt)))
        return filter_updates

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        return self._tracker_player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return self._tracker_configuration_widget

    def copy(self, new_parent: UIPage) -> UIWidget:
        w = AutoTrackerUIWidget(new_parent, self._tracker_player_widget.instance.settings.as_dict())
        w.set_filter(self._associated_filter, 0)
        return w

    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        return self._tracker_player_widget
