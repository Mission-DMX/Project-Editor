"""Scope window for live inspection of filter output channel values."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from controller.network import NetworkManager
from model.broadcaster import Broadcaster
from model.color_hsi import ColorHSI
from model.filter import DataType
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorLabel

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent

    from model.board_configuration import BoardConfiguration

logger = getLogger(__name__)


class _ScopeListItemWidget(QWidget):
    """Row widget inside the scope list: channel label, value, remove button."""

    removed: Signal = Signal(QListWidgetItem)

    def __init__(self, channel_id: str, data_type: DataType, list_item: QListWidgetItem,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._list_item = list_item
        self._data_type = data_type

        layout = QHBoxLayout()
        layout.setContentsMargins(2, 1, 2, 1)

        self._channel_label = QLabel(channel_id)
        layout.addWidget(self._channel_label)
        layout.addStretch()

        self._value_label = QLabel("—")
        layout.addWidget(self._value_label)

        self._color_label: ColorLabel | None = None
        if data_type == DataType.DT_COLOR:
            self._color_label = ColorLabel()
            self._color_label.setFixedWidth(24)
            self._color_label.setFixedHeight(16)
            layout.addWidget(self._color_label)

        remove_button = QToolButton()
        remove_button.setText("X")
        remove_button.setToolTip("Remove this probe")
        remove_button.clicked.connect(lambda: self.removed.emit(self._list_item))
        layout.addWidget(remove_button)

        self.setLayout(layout)

    def set_value(self, raw_value: str) -> None:
        """Parse the raw value according to the channel's data type and display it."""
        try:
            if self._data_type == DataType.DT_COLOR:
                color = ColorHSI.from_filter_str(raw_value, strict=True)
                self._value_label.setText(color.format_for_filter())
                if self._color_label is not None:
                    self._color_label.set_color(color)
            elif self._data_type == DataType.DT_DOUBLE:
                self._value_label.setText(f"{float(raw_value):.3f}")
            else:
                self._value_label.setText(str(int(raw_value)))
        except (ValueError, TypeError) as exc:
            logger.debug("Failed to parse scope value %r for %s: %s",
                         raw_value, self._data_type, exc)
            self._value_label.setText(raw_value)


class ScopeWindow(QDialog):
    """Tool window for live-probing filter output channel values."""

    def __init__(self, parent: QWidget, board_configuration: BoardConfiguration) -> None:
        """Build the scope window.

        Args:
            parent: Qt parent widget.
            board_configuration: Current board configuration, used to look up
                filter data types for picked channels.

        """
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Scope")
        self._board_configuration = board_configuration
        self._broadcaster = Broadcaster()

        layout = QVBoxLayout()

        top_row = QHBoxLayout()
        self._add_button = QPushButton("+")
        self._add_button.setToolTip("Pick a connection in the active editor")
        self._add_button.clicked.connect(self._broadcaster.scope_edge_pick_requested.emit)
        top_row.addWidget(self._add_button)

        self._rate_combo = QComboBox()
        self._rate_combo.addItem("5 s", 5000)
        self._rate_combo.addItem("1 s", 1000)
        self._rate_combo.addItem("0.5 s", 500)
        self._rate_combo.currentIndexChanged.connect(self._on_rate_changed)
        top_row.addWidget(self._rate_combo)
        top_row.addStretch()

        layout.addLayout(top_row)

        self._list = QListWidget()
        layout.addWidget(self._list)

        self.setLayout(layout)
        self.resize(400, 300)

        self._timer = QTimer(self)
        self._timer.setInterval(self._rate_combo.currentData())
        self._timer.timeout.connect(self._poll)
        self._timer.start()

        self._broadcaster.scope_edge_picked.connect(self._add_item)
        self._broadcaster.channel_scope_value_received.connect(self._update_item_value)
        self._broadcaster.active_scene_switched.connect(self._on_active_scene_switched)

    def _on_rate_changed(self) -> None:
        self._timer.setInterval(self._rate_combo.currentData())

    def _poll(self) -> None:
        nm = NetworkManager()
        for row in range(self._list.count()):
            item = self._list.item(row)
            if isinstance(item, AnnotatedListWidgetItem):
                channel_id, _ = item.annotated_data
                nm.request_channel_scope(channel_id)

    def _add_item(self, channel_id: str, data_type: DataType | None) -> None:
        if data_type is None:
            logger.warning("No data type for %s; skipping probe", channel_id)
            return
        for row in range(self._list.count()):
            existing = self._list.item(row)
            if isinstance(existing, AnnotatedListWidgetItem) and existing.annotated_data[0] == channel_id:
                return

        item = AnnotatedListWidgetItem(self._list)
        item.annotated_data = (channel_id, data_type)
        widget = _ScopeListItemWidget(channel_id, data_type, item)
        widget.removed.connect(self._remove_item)
        item.setSizeHint(widget.sizeHint())
        self._list.setItemWidget(item, widget)

    def _remove_item(self, item: QListWidgetItem) -> None:
        row = self._list.row(item)
        if row >= 0:
            self._list.takeItem(row)

    def _update_item_value(self, channel_id: str, raw_value: str) -> None:
        for row in range(self._list.count()):
            item = self._list.item(row)
            if not isinstance(item, AnnotatedListWidgetItem):
                continue
            if item.annotated_data[0] != channel_id:
                continue
            widget = self._list.itemWidget(item)
            if isinstance(widget, _ScopeListItemWidget):
                widget.set_value(raw_value)

    def _on_active_scene_switched(self, _scene_id: int) -> None:
        self._list.clear()
        self._broadcaster.scope_edge_pick_cancelled.emit()

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        self._timer.stop()
        self._broadcaster.scope_edge_pick_cancelled.emit()
        super().closeEvent(event)
