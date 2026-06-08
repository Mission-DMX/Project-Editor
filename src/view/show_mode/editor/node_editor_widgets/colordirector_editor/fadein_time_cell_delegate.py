"""Item Delegate for fade time display."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDoubleSpinBox, QStyledItemDelegate

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QLocale, QModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem, QWidget

class FadeinTimeCellDelegate(QStyledItemDelegate):
    """Presents formatted view to fadein time properties of presets table."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize."""
        super().__init__(parent)
        # TODO allow jogwheel to edit fade-in time

    @override
    def displayText(self, value: str, locale: QLocale, /) -> str:
        fade_in_time = int(value)
        return f"{(fade_in_time * 40) / 1000:.3f}s"

    @override
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex, /) -> QWidget:
        editor = QDoubleSpinBox(parent)
        editor.setMinimum(0)
        editor.setSingleStep(1)
        return editor

    @override
    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex, /) -> None:
        value = index.data(Qt.ItemDataRole.EditRole)
        fade_in_time = int(value)
        editor.setValue((fade_in_time * 40) / 1000)

    @override
    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractItemModel, index: QModelIndex, /) -> None:
        value = editor.value()
        steps = int((value * 1000) / 40)
        model.setData(index, steps, Qt.ItemDataRole.EditRole)
