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
    color presets change. In addition, the widget refreshes itself whenever the model emits its
    configuration_changed signal (see _refresh_stale_table).

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
        self._model.configuration_changed.mapped_signal.connect(self._refresh_stale_table)

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
        """Add a table row displaying the preset selection of a single recall.

        Args:
            recall_index: The index of the recall displayed by the row.
            recall_data: The preset index stored by the recall for every color group.

        """
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
        """Add a new recall to the model.

        The table refreshes itself using the configuration_changed signal emitted by the model.

        """
        self._model.add_recall()

    def _update_remove_recall_button(self) -> None:
        """Enable the remove button if a recall row is currently selected."""
        self._remove_recall_button.setEnabled(0 <= self._recall_table.currentRow() < len(self._model.recalls))

    def _remove_selected_recall(self) -> None:
        """Remove the currently selected recall.

        The table refreshes itself using the configuration_changed signal emitted by the model.

        """
        recall_index = self._recall_table.currentRow()
        if not 0 <= recall_index < len(self._model.recalls):
            return
        self._model.remove_recall(recall_index)

    def _refresh_stale_table(self) -> None:
        """Synchronize the recall table with the current model state.

        Cell values differing from the model are updated in place: This preserves the current selection and
        open cell editors while the table stays in sync with changes made externally, e.g. by filter messages
        received from the network. The table is rebuilt completely only if its structure no longer matches the
        model, e.g. after recalls or color groups were added or removed.

        """
        group_count = len(self._model.output_groups)
        recall_count = len(self._model.recalls)
        self.setEnabled(len(self._model.presets) > 0)
        if self._recall_table.columnCount() != group_count + 1 or self._recall_table.rowCount() != recall_count:
            self.update_recall_table()
            return
        preset_count = len(self._model.presets)
        for row, recall_data in enumerate(self._model.recalls):
            for group_index, value in enumerate(recall_data):
                item = self._recall_table.item(row, group_index + 1)
                if item is None:
                    self.update_recall_table()
                    return
                displayed_value = str(bound_preset_index(value, preset_count))
                if item.text() != displayed_value:
                    item.setText(displayed_value)
