"""Contains RecallCellDelegate class."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyledItemDelegate

from model.virtual_filters.colordirector_vfilter import bound_preset_index
from view.utility_widgets.jogwheel_spinbox import JogwheelSpinBox

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem, QWidget

    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter


class RecallCellDelegate(QStyledItemDelegate):
    """Delegate to provide limited number editing for recall table."""

    def __init__(self, parent: QWidget, model: ColordirectorVFilter) -> None:
        """Initialize."""
        super().__init__(parent)
        self._model: ColordirectorVFilter = model

    @override
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex, /
    ) -> QWidget:
        editor = JogwheelSpinBox(parent)
        editor.setMinimum(0)
        editor.setSingleStep(1)
        editor.setMaximum(max(len(self._model.presets) - 1, 0))
        return editor

    @override
    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex, /) -> None:
        if not isinstance(editor, JogwheelSpinBox):
            return
        value = index.data(Qt.ItemDataRole.EditRole)
        if value is None:
            return
        editor.setValue(int(value))

    @override
    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex, /
    ) -> None:
        if not isinstance(editor, JogwheelSpinBox):
            return
        recall_index: int = index.row()
        group_index: int = index.column() - 1
        if group_index < 0 or not 0 <= recall_index < len(self._model.recalls):
            return
        self._model.normalize_recall(recall_index)
        recall = self._model.recalls[recall_index]
        if group_index >= len(recall):
            return
        value = bound_preset_index(editor.value(), len(self._model.presets))
        model.setData(index, value, Qt.ItemDataRole.EditRole)
        recall[group_index] = value
