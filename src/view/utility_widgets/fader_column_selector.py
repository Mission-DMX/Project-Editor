
"""This file provides a widget to browse bank set columns."""
from logging import getLogger
from typing import Type

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from model.control_desk import BankSet, ColorDeskColumn, DeskColumn, RawDeskColumn
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem

logger = getLogger(__file__)


class FaderColumnSelectorWidget(QWidget):
    """This widget enables the user to select a fader column."""

    selection_changed = Signal(DeskColumn)

    def __init__(self, parent: QWidget | None = None, column_filter: Type[DeskColumn] | None = None,
                 base_set: BankSet | None = None):
        """Construct a new browser widget.

        :param parent: The parent widget of this one
        :param column_filter: an optional column type to filter for
        :param base_set: Display this set even if it is not linked to fish.
        """
        super().__init__()
        self._filter = column_filter
        self._base_sets: list[BankSet] = base_set if isinstance(base_set, list) \
            else [base_set] if isinstance(base_set, BankSet) else []
        self._item_index: dict[str, dict[str, AnnotatedTreeWidgetItem]] = {}

        layout = QVBoxLayout()

        self._tree = QTreeWidget(parent=parent)
        self._tree.setColumnCount(2)
        self._tree.setHeaderLabels(["ID", "Description"])
        self._tree.itemSelectionChanged.connect(self._selection_changed_handler)
        layout.addWidget(self._tree)

        self._ignore_main_brightness_checkbox = QCheckBox("Ignore Main Brightness")
        self._ignore_main_brightness_checkbox.setEnabled(False)
        layout.addWidget(self._ignore_main_brightness_checkbox)
        self.setLayout(layout)
        self.selected_item: AnnotatedTreeWidgetItem | None = None
        self.reload_data()
        # TODO add button to add a new column right in this widget

    def _selection_changed_handler(self, *args):
        item = self._tree.selectedItems()[0]
        if isinstance(item, AnnotatedTreeWidgetItem):
            self.selected_item = item
            self.selection_changed.emit(item.annotated_data)

    @property
    def ignore_main_brightness(self) -> bool:
        """:returns: True if the user selected to ignore the main brightness fader."""
        return self._ignore_main_brightness_checkbox.isChecked()

    @ignore_main_brightness.setter
    def ignore_main_brightness(self, new_value: bool):
        self._ignore_main_brightness_checkbox.setChecked(new_value)

    @property
    def main_brightness_cb_enabled(self) -> bool:
        """Is the checkbox to ignore the main brightness fader enabled itself?"""
        return self._ignore_main_brightness_checkbox.isEnabled()

    @main_brightness_cb_enabled.setter
    def main_brightness_cb_enabled(self, new_value: bool):
        self._ignore_main_brightness_checkbox.setEnabled(new_value)

    def set_selected_item(self, set_id: str, column_id: str):
        """Use this method to select a specified column.

        If there is no matching column, it will simply do nothing.
        If there is a matching one, it will also expand the tree up to the selected one.

        :param set_id: The id of the bank set that contains the column
        :param column_id: The id of the column to select.
        """
        bank_set = self._item_index.get(set_id)
        if bank_set is None:
            return
        column = bank_set.get(column_id)
        if column is None:
            return
        self.selected_item = column
        if self.selected_item:
            self.selected_item.setSelected(True)
            current_item_to_expand = self.selected_item
            while current_item_to_expand:
                current_item_to_expand.setExpanded(True)
                current_item_to_expand = current_item_to_expand.parent()

    def reload_data(self):
        """Refresh the displayed data."""
        self._tree.clear()
        bank_sets_to_search: set[BankSet] = set()
        for bs in BankSet.get_linked_bank_sets():
            bank_sets_to_search.add(bs)
        for bs in self._base_sets:
            bank_sets_to_search.add(bs)
        for bank_set in bank_sets_to_search:
            set_item = QTreeWidgetItem(self._tree)
            set_item.setText(0, bank_set.id)
            set_item.setText(1, str(bank_set.description))
            set_item.setData(0, 0, bank_set)
            i: int = 0
            if not self._item_index.get(bank_set.id):
                self._item_index[bank_set.id] = {}
            for bank in bank_set.banks:
                bank_item = QTreeWidgetItem(set_item)
                bank_item.setText(0, str(i))
                bank_item.setText(1, "")
                for column in bank.columns:
                    if self._filter and not isinstance(column, self._filter):
                        continue
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
                    self._item_index[bank_set.id][column.id] = column_item
                set_item.addChild(bank_item)
                i += 1
            self._tree.insertTopLevelItem(0, set_item)

    def add_base_bank_set(self, bs: BankSet):
        """
        Use this method to add a bank set to the list of force-active sets after construction finished.

        :param bs: The bank set to add.
        """
        if bs is None:
            logger.warning("Tried to add None type base bank set.")
            return
        if bs not in self._base_sets:
            self._base_sets.append(bs)
