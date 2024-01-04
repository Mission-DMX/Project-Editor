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
        self.config_widget = AutoTrackDialogWidget()

    def generate_update_content(self) -> list[tuple[str, str]]:
        pass

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        return self.config_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        return self.config_widget

    def copy(self, new_parent: UIPage) -> UIWidget:
        pass

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        return self.config_widget
