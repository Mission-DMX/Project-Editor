from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from model import DataType

if TYPE_CHECKING:
    from model.filter_data.sequencer.sequencer_channel import SequencerChannel


class ChannelLabel(QWidget):
    """Label to represent a sequencer channel in a QListWidget."""

    _CHANNEL_STYLE_8BIT = """
    background-color: #202020;
    color: #DDDDDD;
    border-radius: 5px;
    padding: 3px;
    """

    _CHANNEL_STYLE_16BIT = """
    background-color: #202020;
    color: #EEEEEE;
    border-radius: 5px;
    padding: 3px;
    """

    _CHANNEL_STYLE_FLOAT = """
    background-color: #202020;
    color: #FFFFFF;
    border-radius: 5px;
    padding: 3px;
    """

    _CHANNEL_STYLE_COLOR = """
    background-color: #202020;
    color: #10AA10;
    border-radius: 5px;
    padding: 3px;
    """

    def __init__(self, channel: "SequencerChannel", parent: QWidget | None = None) -> None:
        """Initialize the channel label using the given channel."""
        QWidget.__init__(self, parent)
        layout = QHBoxLayout(self)
        dtype_label = QLabel(self)
        dtype_label.setText(channel.data_type.format_for_filters())
        dtype_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        match channel.data_type:
            case DataType.DT_DOUBLE:
                dtype_label.setStyleSheet(self._CHANNEL_STYLE_FLOAT)
            case DataType.DT_COLOR:
                dtype_label.setStyleSheet(self._CHANNEL_STYLE_COLOR)
            case DataType.DT_16_BIT:
                dtype_label.setStyleSheet(self._CHANNEL_STYLE_16BIT)
            case DataType.DT_8_BIT:
                dtype_label.setStyleSheet(self._CHANNEL_STYLE_8BIT)
            case _:
                dtype_label.setStyleSheet(self._CHANNEL_STYLE_8BIT)
        dtype_label.setFixedWidth(64)
        layout.addWidget(dtype_label)
        layout.addSpacing(10)
        name_label = QLabel(channel.name)
        layout.addWidget(name_label)
        self.setLayout(layout)
        self.setToolTip(f"Channel {channel.name}\n"
                        f"Data Type: {channel.data_type.name}\n"
                        f"Default Value: {channel.default_value}\n"
                        f"Apply Default On Empty: {channel.apply_default_on_empty}\n"
                        f"Apply Default on Scene Switch: {channel.apply_default_on_scene_switch}\n"
                        f"Interleave Method: {channel.interleave_method.name}")
