"""
This file provides the column input filter settings widget.
"""

from PySide6.QtWidgets import QWidget

from model import Filter
from view.utility_widgets.fader_column_selector import FaderColumnSelectorWidget
from .node_editor_widget import NodeEditorFilterConfigWidget


class ColumnSelect(NodeEditorFilterConfigWidget):
    """This class is an adapter to configure the column select filter with the column selection widget."""

    def _load_parameters(self, parameters: dict[str, str]) -> None:
        pass

    def _get_parameters(self) -> dict[str, str]:
        return {}

    def get_widget(self) -> QWidget:
        return self._widget

    def __init__(self, filter: Filter, parent: QWidget = None):
        super().__init__()
        self._widget = FaderColumnSelectorWidget(parent=parent, base_set=filter.scene.linked_bankset)
        self._filter = filter

    def _load_configuration(self, conf) -> None:
        if "ignore_main_brightness_control" in conf:
            self._widget.main_brightness_cb_enabled = True
            self._widget.ignore_main_brightness = conf.get("ignore_main_brightness_control") == "true"
        set_id = conf.get("set_id") if "set_id" in conf else ""
        column_id = conf.get("column_id") if "column_id" in conf else ""
        self._widget.add_base_bank_set(self._filter.scene.linked_bankset)
        self._widget.reload_data()
        self._widget.set_selected_item(set_id, column_id)

    def _get_configuration(self) -> dict[str, str]:
        if not self._widget.selected_item:
            return {}
        column = self._widget.selected_item.annotated_data
        data = {
            "column_id": column.id,
            "set_id": column.bank_set.id if column.bank_set else "",
            "ignore_main_brightness_control": "true" if self._widget.ignore_main_brightness else "false"
        }
        return data
