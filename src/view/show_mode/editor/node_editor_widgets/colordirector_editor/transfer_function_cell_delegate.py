"""Item delegate for transfer function display."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate

from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QLocale, QModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem, QWidget


class TransferFunctionCellDelegate(QStyledItemDelegate):
    """Allows editing of transfer function using reasonable widget"""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

    @override
    def displayText(self, value: TransferFunction, locale: QLocale, /) -> str:
        return value.value.upper()

    @override
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex, /) -> QWidget:
        widget = QComboBox(parent)
        widget.addItems(TransferFunction.values())
        widget.setEditable(False)
        return widget

    @override
    def setEditorData(self, editor: QComboBox, index: QModelIndex, /) -> None:
        editor.setCurrentText(index.data(Qt.ItemDataRole.EditRole).value)

    @override
    def setModelData(self, editor: QComboBox, model: QAbstractItemModel, index: QModelIndex, /) -> None:
        tf = TransferFunction(editor.currentText())
        model.setData(index, tf, Qt.ItemDataRole.EditRole)
