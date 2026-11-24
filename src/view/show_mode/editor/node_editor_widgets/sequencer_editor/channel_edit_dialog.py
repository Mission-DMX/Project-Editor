"""Contains ChannelEditDialog."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QPushButton,
    QSpinBox,
    QWidget,
)

from model import DataType
from model.color_hsi import ColorHSI
from model.filter_data.sequencer.sequencer_channel import SequencerChannel
from view.show_mode.editor.node_editor_widgets.sequencer_editor.channel_label import ChannelLabel
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorLabel

if TYPE_CHECKING:
    from PySide6 import QtGui
    from PySide6.QtWidgets import QListWidget

    from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem


class ChannelEditDialog(QDialog):
    """Dialog to add mutable channel properties."""

    def __init__(self, channel_item: AnnotatedListWidgetItem, list_widget: QListWidget,
                 parent: QWidget | None = None) -> None:
        """Initialize the dialog but does not open it."""
        super().__init__(parent)
        self._color_dialog: QColorDialog | None = None
        self._channel_item = channel_item
        self._parent_list_widget = list_widget
        if not isinstance(channel_item.annotated_data, SequencerChannel):
            raise ValueError("Expected to be provided with a SequencerChannel")
        self._channel: SequencerChannel = channel_item.annotated_data
        layout = QFormLayout()
        if self._channel.data_type == DataType.DT_COLOR:
            self._cl = ColorLabel()
            self._cl.set_color(self._channel.default_value)
            layout.addRow("Default Color", self._cl)
            change_color_button = QPushButton("Change")
            change_color_button.clicked.connect(self._change_color_clicked)
            layout.addRow(change_color_button)
        elif self._channel.data_type in [DataType.DT_8_BIT, DataType.DT_16_BIT]:
            self._number_tb = QSpinBox()
            self._number_tb.setRange(0, 255 if self._channel.data_type == DataType.DT_8_BIT else 65535)
            self._number_tb.setSingleStep(1)
            self._number_tb.setValue(self._channel.default_value)
            self._number_tb.valueChanged.connect(self._number_value_changed)
            layout.addRow("Default Value:", self._number_tb)
        else:
            self._number_tb = QDoubleSpinBox()
            self._number_tb.setValue(self._channel.default_value)
            self._number_tb.valueChanged.connect(self._number_value_changed)
            layout.addRow("Default Value:", self._number_tb)

        self._apply_on_empty_cb = QCheckBox("Apply on empty transition list")
        self._apply_on_empty_cb.setChecked(self._channel.apply_default_on_empty)
        self._apply_on_empty_cb.stateChanged.connect(self._apply_on_empty_changed)
        layout.addWidget(self._apply_on_empty_cb)

        self._apply_on_scene_switch_cb = QCheckBox("Apply on scene switch")
        self._apply_on_scene_switch_cb.setChecked(self._channel.apply_default_on_scene_switch)
        self._apply_on_scene_switch_cb.stateChanged.connect(self._apply_on_scene_switch_changed)
        layout.addWidget(self._apply_on_scene_switch_cb)

        close_button = QPushButton("Done")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        self.setLayout(layout)

    def _change_color_clicked(self) -> None:
        self._color_dialog = QColorDialog()
        self._color_dialog.setCurrentColor(self._channel.default_value.to_qt_color())
        self._color_dialog.setModal(True)
        self._color_dialog.accepted.connect(self._color_selected)
        self._color_dialog.show()

    def _color_selected(self) -> None:
        self._channel.default_value = ColorHSI.from_qt_color(self._color_dialog.currentColor())
        self._cl.set_color(self._channel.default_value)
        self._color_dialog = None

    def _number_value_changed(self) -> None:
        self._channel.default_value = self._number_tb.value()

    def _apply_on_empty_changed(self) -> None:
        self._channel.apply_default_on_empty = self._apply_on_empty_cb.isChecked()

    def _apply_on_scene_switch_changed(self) -> None:
        self._channel.apply_default_on_scene_switch = self._apply_on_scene_switch_cb.isChecked()

    @override
    def closeEvent(self, event: QtGui.QCloseEvent, /) -> None:
        self._parent_list_widget.setItemWidget(
            self._channel_item,
            ChannelLabel(self._channel, self._parent_list_widget)
        )
        super().closeEvent(event)
