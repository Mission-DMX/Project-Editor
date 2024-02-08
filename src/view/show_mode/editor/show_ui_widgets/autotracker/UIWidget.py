from PySide6.QtWidgets import QWidget

from model import UIWidget, UIPage
from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
from view.show_mode.editor.show_ui_widgets.autotracker.AutoTrackDialogWidget import AutoTrackDialogWidget


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
        self.config_widget = AutoTrackDialogWidget()

    def generate_update_content(self) -> list[tuple[str, str]]:
        filter_updates = []
        for tracker_id in range(self._associated_filter.number_of_concurrent_trackers):
            pan_filter_id = self._associated_filter.get_pan_filter_id(tracker_id)
            tilt_filter_id = self._associated_filter.get_tilt_filter_id(tracker_id)
            if not pan_filter_id or not tilt_filter_id:
                continue
            filter_updates.append((pan_filter_id, str(0)))  # TODO query real value based on data type
            filter_updates.append((tilt_filter_id, str(0)))  # TODO query real value based on data type
        return filter_updates

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        return self.config_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return self.config_widget

    def copy(self, new_parent: UIPage) -> UIWidget:
        # TODO
        pass

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        return self.config_widget
