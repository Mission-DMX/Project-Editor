"""Label for sequencer channels."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

import style
from model import DataType

if TYPE_CHECKING:
    from model.filter_data.sequencer.sequencer_channel import SequencerChannel


def generate_datatype_label(parent: QWidget, channel_data_type: DataType) -> QLabel:
    """Generate a styled channel data type label.

    Args:
        parent: The parent of the widget.
        channel_data_type: The data type to represent.

    """
    dtype_label = QLabel(parent)
    dtype_label.setText(channel_data_type.format_for_filters())
    dtype_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    match channel_data_type:
        case DataType.DT_DOUBLE:
            dtype_label.setStyleSheet(style.CHANNEL_STYLE_FLOAT)
        case DataType.DT_COLOR:
            dtype_label.setStyleSheet(style.CHANNEL_STYLE_COLOR)
        case DataType.DT_16_BIT:
            dtype_label.setStyleSheet(style.CHANNEL_STYLE_16BIT)
        case DataType.DT_8_BIT:
            dtype_label.setStyleSheet(style.CHANNEL_STYLE_8BIT)
        case _:
            dtype_label.setStyleSheet(style.CHANNEL_STYLE_8BIT)
    dtype_label.setFixedWidth(64)
    return dtype_label

class ChannelLabel(QWidget):
    """Label to represent a sequencer channel in a QListWidget."""

    def __init__(self, channel: SequencerChannel, parent: QWidget | None = None) -> None:
        """Initialize the channel label using the given channel."""
        QWidget.__init__(self, parent)
        layout = QHBoxLayout(self)
        channel_data_type = channel.data_type
        dtype_label = generate_datatype_label(self, channel_data_type)
        layout.addWidget(dtype_label)
        layout.addSpacing(10)
        name_label = QLabel(channel.name)
        layout.addWidget(name_label)
        self.setLayout(layout)
        self.setToolTip(channel.tooltip)
