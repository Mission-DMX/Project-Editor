"""Sequencer control show UI widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from model import UIWidget

if TYPE_CHECKING:
    from model import UIPage
    from proto import FilterMode_pb2


class SequencerControlUIWidget(UIWidget):
    """Information Widget for an associated sequencer.

    Most notably the current running transitions.
    """

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Initialize the sequence control widget.

        :param parent: The parent widget page.
        :param configuration: The initial configuration of the sequencer.
        """
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None
        self._player_list: QListWidget | None = None

    def generate_update_content(self) -> list[tuple[str, str]]:
        """Generate messages to be sent to the filter.

        As this widget only displays information at the moment, this does nothing.
        """
        return []

    def _construct_widget(self, parent: QWidget | None, for_player: bool) -> QWidget:
        """Generate a widget to use. Primary a list widget and labels."""
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
            self.parent.scene.board_configuration.register_filter_update_callback(
                self.parent.scene.scene_id, self.filter_ids[0], self._update_received
            )
        layout.addWidget(list_widget)
        w.setLayout(layout)
        return w

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        """Return the player widget."""
        self._player_widget = self._construct_widget(parent, True)
        return self._player_widget

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        """Return the configuration widget."""
        self._configuration_widget = self._construct_widget(parent, False)
        return self._configuration_widget

    def copy(self, new_parent: UIPage) -> UIWidget:
        """Return a copy of this show ui widget."""
        new_widget = SequencerControlUIWidget(new_parent, self.configuration.copy())
        self.copy_base(new_widget)
        return new_widget

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        """As there's nothing to configure at the moment, this method returns an empty widget."""
        # TODO should we provide configuration options?
        return QWidget(parent=parent)

    def _update_received(self, param: FilterMode_pb2.update_parameter) -> None:
        """Refresh the current sequence list on new updates from the filter."""
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

    def close(self) -> None:
        """Deregister the update request upon close."""
        if self._player_list is None:
            return
        self.parent.scene.board_configuration.remove_filter_update_callback(
            self.parent.scene.scene_id, self.filter_ids[0], self._update_received
        )
