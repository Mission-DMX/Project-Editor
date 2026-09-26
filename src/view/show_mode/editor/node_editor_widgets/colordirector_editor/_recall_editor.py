"""Contains widget to edit saved recalls."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QVBoxLayout, QWidget

from model.virtual_filters.colordirector_vfilter import bound_preset_index
from view.show_mode.editor.node_editor_widgets.colordirector_editor.recall_cell_delegate import RecallCellDelegate
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTableWidgetItem

if TYPE_CHECKING:
    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter


class RecallEditWidget(QWidget):
    """Enable editing of recalls.

    The widget disables itself if no presets are present. Otherwise, it will populate itself.
    The owning editor widget refreshes the table using update_recall_table whenever the output groups or the
    color presets change.

    """

    def __init__(self, model: ColordirectorVFilter, parent: QWidget | None = None) -> None:
        """Initialize using given model and optional parent."""
        super().__init__(parent)
        self._model: ColordirectorVFilter = model
        layout = QVBoxLayout()
        buttons_layout = QHBoxLayout()
        self._add_recall_button = QPushButton("Add")
        self._add_recall_button.clicked.connect(self._add_recall)
        buttons_layout.addWidget(self._add_recall_button)
        self._remove_recall_button = QPushButton("Remove")
        self._remove_recall_button.clicked.connect(self._remove_selected_recall)
        self._remove_recall_button.setEnabled(False)
        buttons_layout.addWidget(self._remove_recall_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        self._recall_table = QTableWidget()
        self._recall_table.setItemDelegate(RecallCellDelegate(self._recall_table, self._model))
        self._recall_table.itemSelectionChanged.connect(self._update_remove_recall_button)
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
            self._add_recall_row_to_table(i, recall_data)
        header_labels: list[str] = ["Recall Number"]
        header_labels.extend(self._model.output_groups.keys())
        self._recall_table.setHorizontalHeaderLabels(header_labels)
        self._update_remove_recall_button()

    def _add_recall_row_to_table(self, recall_index: int, recall_data: list[int]) -> None:
        index_item = AnnotatedTableWidgetItem(str(recall_index))
        # recall index, color group index, color preset index
        index_item.annotated_data = (recall_index, -1, -1)
        index_item.setFlags(index_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        self._recall_table.setItem(recall_index, 0, index_item)
        self._model.normalize_recall(recall_index)
        preset_count = len(self._model.presets)
        for group_index, value in enumerate(recall_data):
            displayed_value = bound_preset_index(value, preset_count)
            step_item = AnnotatedTableWidgetItem(str(displayed_value))
            step_item.annotated_data = (recall_index, group_index, value)
            self._recall_table.setItem(recall_index, group_index + 1, step_item)

    def _add_recall(self) -> None:
        recall_data = self._model.add_recall()
        self._recall_table.setRowCount(len(self._model.recalls))
        self._add_recall_row_to_table(len(self._model.recalls) - 1, recall_data)

    def _update_remove_recall_button(self) -> None:
        """Enable the remove button if a recall row is currently selected."""
        self._remove_recall_button.setEnabled(0 <= self._recall_table.currentRow() < len(self._model.recalls))

    def _remove_selected_recall(self) -> None:
        """Remove the currently selected recall."""
        recall_index = self._recall_table.currentRow()
        if not 0 <= recall_index < len(self._model.recalls):
            return
        self._model.remove_recall(recall_index)
        self.update_recall_table()
