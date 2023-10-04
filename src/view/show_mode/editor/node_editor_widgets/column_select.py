from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QCheckBox

from model import Filter
from model.control_desk import BankSet, RawDeskColumn, ColorDeskColumn
from .node_editor_widget import NodeEditorFilterConfigWidget
from ..show_browser.annotated_item import AnnotatedTreeWidgetItem


class ColumnSelect(NodeEditorFilterConfigWidget):
    def _load_parameters(self, parameters: dict[str, str]):
        return dict()

    def _get_parameters(self) -> dict[str, str]:
        return dict()

    def get_widget(self) -> QWidget:
        return self._widget

    def __init__(self, filter: Filter, parent: QWidget = None):
        super().__init__()
        self._widget = QWidget()
        layout = QVBoxLayout()

        self._tree = QTreeWidget(parent=parent)
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["ID", "Description"])
        self._tree.itemSelectionChanged.connect(self._selection_changed_handler)
        layout.addWidget(self._tree)

        self._ignore_main_brightness_checkbox = QCheckBox("Ignore Main Brightness")
        self._ignore_main_brightness_checkbox.setEnabled(False)
        layout.addWidget(self._ignore_main_brightness_checkbox)
        self._widget.setLayout(layout)
        self._selected_item: AnnotatedTreeWidgetItem | None = None
        self._filter = filter

    def _load_configuration(self, conf):
        if "ignore_main_brightness_control" in conf.keys():
            self._ignore_main_brightness_checkbox.setEnabled(True)
            self._ignore_main_brightness_checkbox.setChecked(conf.get("ignore_main_brightness_control") == "true")
        set_id = conf.get("set_id") if "set_id" in conf.keys() else ""
        column_id = conf.get("column_id") if "column_id" in conf.keys() else ""
        self._tree.clear()

        bank_sets_to_search: set[BankSet] = set()
        for bs in BankSet.get_linked_bank_sets():
            bank_sets_to_search.add(bs)
        bank_sets_to_search.add(self._filter.scene.linked_bankset)
        for bank_set in bank_sets_to_search:
            set_item = QTreeWidgetItem(self._tree)
            set_item.setText(0, bank_set.id)
            set_item.setText(1, str(bank_set.description))
            set_item.setData(0, 0, bank_set)
            correct_set: bool = bank_set.id == set_id
            i: int = 0
            for bank in bank_set.banks:
                bank_item = QTreeWidgetItem(set_item)
                bank_item.setText(0, str(i))
                bank_item.setText(1, "")
                for column in bank.columns:
                    correct_column = column.id == column_id
                    column_item = AnnotatedTreeWidgetItem(bank_item)
                    column_item.setText(0, str(column.display_name) if column.display_name else "No Name")
                    if isinstance(column, RawDeskColumn):
                        column_type_str = "RAW"
                    elif isinstance(column, ColorDeskColumn):
                        column_type_str = "Color HSI"
                    else:
                        column_type_str = "?"
                    column_item.setText(1, column_type_str)
                    column_item.annotated_data = column
                    bank_item.addChild(column_item)
                    if correct_column and correct_set:
                        self._selected_item = column_item
                set_item.addChild(bank_item)
                i += 1
            self._tree.insertTopLevelItem(0, set_item)
        if self._selected_item:
            self._selected_item.setSelected(True)
            current_item_to_expand = self._selected_item
            while current_item_to_expand:
                current_item_to_expand.setExpanded(True)
                current_item_to_expand = current_item_to_expand.parent()

    def _get_configuration(self) -> dict[str, str]:
        if not self._selected_item:
            return dict()
        column = self._selected_item.annotated_data
        data = {
            "column_id": column.id,
            "set_id": self._selected_item.parent().parent().data(0, 0).id,
            "ignore_main_brightness_control": "true" if self._ignore_main_brightness_checkbox.isChecked() else "false"
        }
        return data

    def _selection_changed_handler(self, *args):
        item = self._tree.selectedItems()[0]
        if isinstance(item, AnnotatedTreeWidgetItem):
            self._selected_item = item
