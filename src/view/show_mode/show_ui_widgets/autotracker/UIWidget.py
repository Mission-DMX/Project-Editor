# coding=utf-8
from logging import getLogger

from PySide6.QtWidgets import QWidget

from model import UIPage, UIWidget
from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
from view.show_mode.show_ui_widgets.autotracker.AutoTrackDialogWidget import AutoTrackDialogWidget
from view.show_mode.show_ui_widgets.autotracker.VFilterLightController import VFilterLightController

logger = getLogger(__file__)


class AutoTrackerUIWidget(UIWidget):

    def __init__(self, fid: str, parent_page: "UIPage", configuration: dict[str, str] = None):
        super().__init__(fid, parent_page, configuration)
        associated_filter = parent_page.scene.get_filter_by_id(fid)
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

    def generate_update_content(self) -> list[tuple[str, str]]:
        filter_updates = []
        lc = self._tracker_player_widget.instance.settings.lights
        if not isinstance(lc, VFilterLightController):
            logger.error("Expected VFilterLightController. Got {} instead.".format(type(lc)))
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
        return AutoTrackerUIWidget(self._associated_filter.filter_id, new_parent,
                                   self._tracker_player_widget.instance.settings.as_dict())

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        return self._tracker_player_widget
