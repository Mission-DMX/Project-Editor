"""Item delegate for transfer function display."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate

from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QLocale, QModelIndex, QPersistentModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem, QWidget


class TransferFunctionCellDelegate(QStyledItemDelegate):
    """Allows editing of transfer function using reasonable widget."""

    @override
    def displayText(self, value: TransferFunction, locale: QLocale | QLocale.Language, /) -> str:
        return value.value.upper()

    @override
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex, /
    ) -> QWidget:
        widget = QComboBox(parent)
        widget.addItems(TransferFunction.values())
        widget.setEditable(False)
        return widget

    @override
    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex, /) -> None:
        if not isinstance(editor, QComboBox):
            return
        value = index.data(Qt.ItemDataRole.EditRole)
        if not isinstance(value, TransferFunction):
            return
        editor.setCurrentText(value.value)

    @override
    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex, /
    ) -> None:
        if not isinstance(editor, QComboBox):
            return
        tf = TransferFunction(editor.currentText())
        model.setData(index, tf, Qt.ItemDataRole.EditRole)
