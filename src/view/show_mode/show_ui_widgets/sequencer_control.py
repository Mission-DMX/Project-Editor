"""Sequencer control show UI widget."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from model import FilterUpdateCallbackMixin, UIWidget

if TYPE_CHECKING:
    from model import Filter, UIPage
    from proto import FilterMode_pb2


class SequencerControlUIWidget(FilterUpdateCallbackMixin, UIWidget):
    """Information Widget for an associated sequencer.

    Most notably the current running transitions.
    """

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        """Sequence control widget.

        Args:
            parent: The parent widget page.
            configuration: The initial configuration of the sequencer.

        """
        super().__init__(parent, configuration)
        self._player_widget: QWidget | None = None
        self._configuration_widget: QWidget | None = None
        self._player_list: QListWidget | None = None

    @override
    def set_filter(self, f: Filter, i: int) -> None:
        """Link the sequencer widget to a filter and start listening to its fish updates."""
        if not f:
            return
        super().set_filter(f, i)
        self._register_fish_callback(f)

    @override
    def notify_id_rename(self, old_id: str, new_id: str) -> None:
        """Move the linked filter id and the fish callback along when the filter is renamed."""
        super().notify_id_rename(old_id, new_id)
        self._handle_filter_id_rename(old_id, new_id)

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
            self._player_list = list_widget
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

    def _update_from_fish(self, param: FilterMode_pb2.update_parameter) -> None:
        """Refresh the current sequence list on new updates from the filter.

        Empty transition names are ignored, and newly appearing transitions are appended in a
        stable (sorted) order.
        """
        player_list = self._player_list
        if player_list is None or param.parameter_key != "active_transition_list":
            return
        try:
            transition_name_list = {name for name in param.parameter_value.split(";") if name}
            item_rows_to_remove = []
            for i in range(player_list.count()):
                item = player_list.item(i)
                if item.text() in transition_name_list:
                    transition_name_list.remove(item.text())
                else:
                    item_rows_to_remove.append(i)
            item_rows_to_remove.sort(reverse=True)
            for i in item_rows_to_remove:
                player_list.takeItem(i)
            del item_rows_to_remove
            for missing_transition in sorted(transition_name_list):
                item = QListWidgetItem()
                item.setText(missing_transition)
                player_list.addItem(item)
        except RuntimeError:
            self._player_list = None
