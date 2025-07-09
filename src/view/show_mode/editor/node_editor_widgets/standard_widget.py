"""TODO"""
from logging import getLogger

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QWidget

from model import Filter
from .node_editor_widget import NodeEditorFilterConfigWidget

logger = getLogger(__name__)


class StandardWidget(NodeEditorFilterConfigWidget):

    def __init__(self, filter_: Filter, parent: QWidget = None):
        self._filter = filter_
        self._widget = QWidget(parent)
        self._widget.setFixedSize(250, 250)
        self._layout = QFormLayout(self._widget)
        self._widget.setLayout(self._layout)

        self._layout.addRow(filter_.filter_id, QLabel("Settings"))

        # Only add initial parameters section if present
        if len(self._filter.initial_parameters) > 0:
            self._layout.addRow("Initial Parameters", QLabel(""))
            for key, value in self._filter.initial_parameters.items():
                line_edit = QLineEdit()
                line_edit.setText(value)
                line_edit.textChanged.connect(lambda new_value, key_=key: self._ip_value_changed(key_, new_value))
                self._layout.addRow(key, line_edit)
        # Only add filter configuration section if present
        if len(self._filter.filter_configurations) > 0:
            self._layout.addRow("Filter Configurations", QLabel(""))
            for key, value in self._filter.filter_configurations.items():
                line_edit = QLineEdit()
                line_edit.setText(value)
                line_edit.textChanged.connect(lambda new_value, key_=key: self._fc_value_changed(key_, new_value))
                self._layout.addRow(key, line_edit)

    def get_widget(self) -> QWidget:
        return self._widget

    def _ip_value_changed(self, key: str, value: str) -> None:
        # TODO remove to direct manipulation of dict
        self._filter.initial_parameters[key] = value

    def _fc_value_changed(self, key: str, value: str) -> None:
        # TODO remove to direct manipulation of dict
        self._filter.filter_configurations[key] = value

    def _get_configuration(self) -> dict[str, str]:
        """Does nothing"""
        pass

    def _load_configuration(self, conf: dict[str, str]) -> None:
        """Does nothing"""
        pass

    def _load_parameters(self, parameters: dict[str, str]) -> None:
        """Does nothing"""
        pass

    def _get_parameters(self) -> dict[str, str]:
        """Does nothing"""
        pass
