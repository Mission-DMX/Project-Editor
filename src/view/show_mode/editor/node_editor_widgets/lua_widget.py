from PySide6.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QVBoxLayout, QListWidget, QToolBar, QComboBox, QLineEdit

from model import DataType
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget


class LuaScriptConfigWidget(NodeEditorFilterConfigWidget):

    def get_widget(self) -> QWidget:
        return self._widget

    def _load_parameters(self, parameters: dict[str, str]):
        self._script_edit_field.setText(parameters["script"])

    def _get_parameters(self) -> dict[str, str]:
        return {"script": self._script_edit_field.toPlainText()}

    def _load_configuration(self, conf: dict[str, str]):
        self._channel_list.clear()
        for in_item in conf["in_mapping"].split(';'):
            channel_name, data_type = in_item.split(':')
            self._channels[channel_name] = (True, DataType.from_filter_str(data_type))
            # TODO replace with AnnotatedListWidgetItem
            self._channel_list.insertItem(0, "{}: input,{}".format(channel_name, data_type))
        for out_item in conf["out_mapping"].split(';'):
            channel_name, data_type = out_item.split(':')
            self._channels[channel_name] = (False, DataType.from_filter_str(data_type))
            self._channel_list.insertItem(0, "{}: output,{}".format(channel_name, data_type))

    def _get_configuration(self) -> dict[str, str]:
        in_maps: list[str] = []
        out_maps: list[str] = []
        for channel_name, channel_props in self._channels:
            is_input: str = channel_props[0]
            dt: DataType = channel_props[1]
            description = "{}:{}".format(channel_name, dt.format_for_filters())
            if is_input:
                in_maps.append(description)
            else:
                out_maps.append(description)
        return {'in_mapping': ";".join(in_maps), 'out_mapping': ";".join(out_maps)}

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self._widget = QWidget(parent)
        self._channels: dict[str, tuple[bool, DataType]] = dict()

        central_layout = QHBoxLayout()
        side_container = QWidget(self._widget)

        side_layout = QVBoxLayout()

        self._toolbar = QToolBar(side_container)
        self._toolbar.addAction("Add Input", self._add_input)
        self._toolbar.addAction("Add Output", self._add_output)
        self._toolbar.addAction("Remove Selected Port")
        # TODO implement removal
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
        self._script_edit_field = QTextEdit(self._widget)
        central_layout.addWidget(self._script_edit_field)
        # TODO add syntax highlighting support
        self._widget.setLayout(central_layout)

    def _add_input(self):
        name = self._new_channel_name.text()
        self._channels[name] = (True, DataType.from_filter_str(self._data_type_combo_box.currentText()))

    def _add_output(self):
        name = self._new_channel_name.text()
        self._channels[name] = (False, DataType.from_filter_str(self._data_type_combo_box.currentText()))
