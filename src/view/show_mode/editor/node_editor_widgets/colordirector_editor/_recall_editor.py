"""Contains widget to edit saved recalls."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QVBoxLayout, QWidget

from view.show_mode.editor.node_editor_widgets.colordirector_editor.recall_cell_delegate import RecallCellDelegate
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTableWidgetItem

if TYPE_CHECKING:
    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter


class RecallEditWidget(QWidget):
    """Enable editing of recalls.

    Widget disables itself when no output groups are detected. Otherwise, it will populate itself.
    When a new group is added, the table needs to be updated.

    """

    def __init__(self, model: ColordirectorVFilter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model: ColordirectorVFilter = model
        layout = QVBoxLayout()
        buttons_layout = QHBoxLayout()
        self._add_recall_button = QPushButton("Add")
        self._add_recall_button.clicked.connect(self._add_recall)
        buttons_layout.addWidget(self._add_recall_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        self._recall_table = QTableWidget()
        self._recall_table.setItemDelegate(RecallCellDelegate(self._recall_table, self._model))
        layout.addWidget(self._recall_table)
        self.setLayout(layout)
        self.update_recall_table()

    def update_recall_table(self) -> None:
        """Update the recall table and enabled state."""
        self.setEnabled(len(self._model.presets) > 0)
        self._recall_table.clear()
        # one for the recall number and one for each group to be updated
        group_count = len(self._model.output_groups)
        self._recall_table.setColumnCount(group_count + 1)
        self._recall_table.setRowCount(len(self._model.recalls))
        for i, recall_data in enumerate(self._model.recalls):
            self._add_recall_row_to_table(group_count, i, recall_data)
        header_labels: list[str] = ["Recall Number"]
        header_labels.extend(self._model.output_groups.keys())
        self._recall_table.setHorizontalHeaderLabels(header_labels)

    def _add_recall_row_to_table(self, group_count: int, recall_index: int, recall_data: list[int]) -> None:
        index_item = AnnotatedTableWidgetItem(str(recall_index))
        # recall index, step in recall, data
        index_item.annotated_data = (recall_index, -1, 0)
        index_item.setFlags(index_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self._recall_table.setItem(recall_index, 0, index_item)
        while len(recall_data) < group_count:
            recall_data.append(0)
        for group_index, value in enumerate(recall_data):
            step_item = AnnotatedTableWidgetItem(str(value))
            step_item.annotated_data = (recall_index, group_index, value)
            self._recall_table.setItem(recall_index, group_index + 1, step_item)

    def _add_recall(self) -> None:
        group_count = len(self._model.output_groups)
        recall_data: list[int] = [0] * group_count
        self._model.recalls.append(recall_data)
        self._recall_table.setRowCount(len(self._model.recalls))
        self._add_recall_row_to_table(group_count, len(self._model.recalls) - 1, recall_data)
