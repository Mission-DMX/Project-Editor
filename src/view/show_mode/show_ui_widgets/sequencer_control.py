from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem

from model import UIWidget
from proto import FilterMode_pb2


class SequencerControlUIWidget(UIWidget):
    def __init__(self, parent: "UIPage", configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None
        self._player_list: QListWidget | None = None

    def generate_update_content(self) -> list[tuple[str, str]]:
        return []

    def _construct_widget(self, parent: QWidget | None, for_player: bool) -> QWidget:
        w = QWidget(parent=parent)
        w.setMinimumWidth(300)
        w.setMinimumHeight(100)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(str(", ".join(self.filter_ids))))
        layout.addWidget(QLabel("Current Active Sequences:"))
        list_widget = QListWidget()
        if for_player:
            self.close()
            self._player_list = list_widget
            self.parent.scene.board_configuration.register_filter_update_callback(self.parent.scene.scene_id, self.filter_ids[0], self._update_received)
        layout.addWidget(list_widget)
        w.setLayout(layout)
        return w

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        self._player_widget = self._construct_widget(parent, True)
        return self._player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        self._configuration_widget = self._construct_widget(parent, False)
        return self._configuration_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        new_widget = SequencerControlUIWidget(new_parent, self.configuration.copy())
        self.copy_base(new_widget)
        return new_widget

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        # TODO should we provide configuration options?
        return QWidget(parent=parent)

    def _update_received(self, param: FilterMode_pb2.update_parameter):
        if self._player_list is not None and param.parameter_key == "active_transition_list":
            transition_name_list = set(param.parameter_value.split(";"))
            item_rows_to_remove = []
            for i in range(self._player_list.count()):
                item = self._player_list.item(i)
                if item.text() in transition_name_list:
                    transition_name_list.remove(item.text())
                else:
                    item_rows_to_remove.append(i)
            item_rows_to_remove.sort(reverse=True)
            for i in item_rows_to_remove:
                self._player_list.takeItem(i)
            del item_rows_to_remove
            for missing_transition in transition_name_list:
                item = QListWidgetItem()
                item.setText(missing_transition)
                self._player_list.addItem(item)

    def close(self):
        if self._player_list is None:
            return
        self.parent.scene.board_configuration.remove_filter_update_callback(self.parent.scene.scene_id, self.filter_ids[0], self._update_received)
