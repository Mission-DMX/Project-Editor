"""Module contains filter config widgets for Lua script fitlers."""
import os
from typing import override

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

import style
from model import DataType
from utility import resource_path
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

from ._lua_syntax_highlighter import LuaSyntaxHighlighter
from .node_editor_widget import NodeEditorFilterConfigWidget
from .sequencer_editor.channel_label import generate_datatype_label


class _ChannelListItemWidget(QWidget):
    """Label widget to display direction type and name of channel."""

    _input_icon = QIcon(resource_path(os.path.join("resources", "icons", "filter-input.svg"))).pixmap(16, 16)
    _output_icon = QIcon(resource_path(os.path.join("resources", "icons", "filter-output.svg"))).pixmap(16, 16)

    def __init__(self, name: str, data_type: DataType, is_input: bool) -> None:
        """Initialize the label."""
        super().__init__()
        layout = QHBoxLayout()
        self._direction_label = QLabel(self)
        self._direction_label.setPixmap(
            _ChannelListItemWidget._input_icon if is_input else _ChannelListItemWidget._output_icon
        )
        self._direction_label.setStyleSheet(style.LABEL_STYLE_BULLET)
        layout.addWidget(self._direction_label)
        layout.addSpacing(10)
        self._dt_label = generate_datatype_label(self, data_type)
        layout.addWidget(self._dt_label)
        layout.addSpacing(10)
        self._name_label = QLabel(name)
        layout.addWidget(self._name_label)
        layout.addStretch()
        self.setLayout(layout)


class LuaScriptConfigWidget(NodeEditorFilterConfigWidget):
    """Code editor and channel setup for Lua filter."""

    @override
    def parent_opened(self) -> None:
        super().parent_opened()

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        self._script_edit_field.setPlainText(parameters["script"])

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {"script": self._script_edit_field.toPlainText()}

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._channel_list.clear()
        self._channels.clear()
        self._new_channel_name.setText("")
        for in_item in conf["in_mapping"].split(";"):
            if not in_item:
                continue
            channel_name, data_type = in_item.split(":")
            self._channels[channel_name] = (True, DataType.from_filter_str(data_type))
            self._insert_channel_in_list(channel_name, data_type, True)
        for out_item in conf["out_mapping"].split(";"):
            if not out_item:
                continue
            channel_name, data_type = out_item.split(":")
            self._channels[channel_name] = (False, DataType.from_filter_str(data_type))
            self._insert_channel_in_list(channel_name, data_type, False)

    def _insert_channel_in_list(self, channel_name: str, data_type: DataType | str, is_input: bool) -> None:
        format_str = "{}: input,{}" if is_input else "{}: output,{}"
        item = AnnotatedListWidgetItem(self._channel_list)
        item.setToolTip(format_str.format(channel_name, data_type))
        if isinstance(data_type, str):
            data_type = DataType.from_filter_str(data_type)
        item.annotated_data = (channel_name, data_type, is_input)
        widget = _ChannelListItemWidget(channel_name, data_type, is_input)
        item.setSizeHint(widget.sizeHint())
        self._channel_list.insertItem(0, item)
        self._channel_list.setItemWidget(item, widget)

    @override
    def _get_configuration(self) -> dict[str, str]:
        in_maps: list[str] = []
        out_maps: list[str] = []
        for channel_name, channel_props in self._channels.items():
            is_input: bool = channel_props[0]
            dt: DataType = channel_props[1]
            description = f"{channel_name}:{dt.format_for_filters()}"
            if is_input:
                in_maps.append(description)
            else:
                out_maps.append(description)
        return {"in_mapping": ";".join(in_maps), "out_mapping": ";".join(out_maps)}

    def __init__(self, parent: QWidget = None) -> None:
        """Initialize config widget using optional parent widget."""
        super().__init__()
        self._widget = QWidget(parent)
        self._channels: dict[str, tuple[bool, DataType]] = {}

        central_layout = QHBoxLayout()
        side_container = QWidget(self._widget)

        side_layout = QVBoxLayout()

        self._toolbar = QToolBar(side_container)
        self._toolbar.addAction("Add Input", self._add_input)
        self._toolbar.addAction("Add Output", self._add_output)
        self._toolbar.addAction("Remove Selected Port", self._remove_channel)
        self._data_type_combo_box = QComboBox(self._toolbar)
        self._data_type_combo_box.addItems(DataType.names())
        self._toolbar.addWidget(self._data_type_combo_box)
        self._new_channel_name = QLineEdit(self._toolbar)
        self._toolbar.addWidget(self._new_channel_name)
        side_layout.addWidget(self._toolbar)

        self._channel_list = QListWidget(side_container)
        side_layout.addWidget(self._channel_list)

        side_container.setLayout(side_layout)
        central_layout.addWidget(side_container)
        self._script_edit_field = QPlainTextEdit(self._widget)
        central_layout.addWidget(self._script_edit_field)
        self._highlighter = LuaSyntaxHighlighter(self._script_edit_field.document())
        self._widget.setLayout(central_layout)

    def _add_input(self) -> None:
        name = self._new_channel_name.text()
        if name and name not in self._channels:
            data_type = DataType.from_filter_str(self._data_type_combo_box.currentText())
            self._channels[name] = (True, data_type)
            self._insert_channel_in_list(name, data_type, True)
        else:
            pass  # TODO error message

    def _add_output(self) -> None:
        name = self._new_channel_name.text()
        if name and name not in self._channels:
            data_type = DataType.from_filter_str(self._data_type_combo_box.currentText())
            self._channels[name] = (False, data_type)
            self._insert_channel_in_list(name, data_type, False)
        else:
            pass  # TODO show appropriate error message

    def _remove_channel(self) -> None:
        for item in self._channel_list.selectedItems().copy():
            if not isinstance(item, AnnotatedListWidgetItem):
                continue
            self._channels.pop(item.annotated_data[0])
            self._channel_list.takeItem(self._channel_list.row(item))
