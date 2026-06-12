"""Contains RecallCellDelegate class."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyledItemDelegate

from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QLocale, QModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem, QWidget

    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter

class RecallCellDelegate(QStyledItemDelegate):
    """Delegate to provide limited number editing for recall table."""

    def __init__(self, parent: QWidget, model: ColordirectorVFilter) -> None:
        """Initialize."""
        super().__init__(parent)
        self._model: ColordirectorVFilter = model

    @override
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex, /) -> QWidget:
        editor = JogwheelSpinBox(parent)
        editor.setMinimum(0)
        editor.setSingleStep(1)
        editor.setMaximum(len(self._model.presets))
        return editor

    @override
    def setEditorData(self, editor: JogwheelSpinBox, index: QModelIndex, /) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        editor.setValue(int(value))

    @override
    def setModelData(self, editor: JogwheelSpinBox, model: QAbstractItemModel, index: QModelIndex, /) -> None:
        value = editor.value()
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        recall_index: int = index.row()
        group_index: int = index.column() - 1
        recall_date = self._model.recalls[recall_index]
        while len(recall_date) < len(self._model.output_groups):
            recall_date.append(0)
        recall_date[group_index] = value
