"""Item Delegate for fade time display."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyledItemDelegate

from model.virtual_filters.colordirector_vfilter import STEP_DURATION_MS
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QLocale, QModelIndex, QPersistentModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem, QWidget


class FadeinTimeCellDelegate(QStyledItemDelegate):
    """Presents formatted view to fadein time properties of presets table."""

    @override
    def displayText(self, value: str, locale: QLocale | QLocale.Language, /) -> str:
        fade_in_time = int(value)
        return f"{(fade_in_time * STEP_DURATION_MS) / 1000:.3f}s"

    @override
    def createEditor(
        self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex, /
    ) -> QWidget:
        editor = JogwheelDoubleSpinBox(parent)
        editor.setMinimum(0)
        editor.setSingleStep(1)
        return editor

    @override
    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex, /) -> None:
        if not isinstance(editor, JogwheelDoubleSpinBox):
            return
        value = index.data(Qt.ItemDataRole.EditRole)
        fade_in_time = int(value)
        editor.setValue((fade_in_time * STEP_DURATION_MS) / 1000)

    @override
    def setModelData(
        self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex | QPersistentModelIndex, /
    ) -> None:
        if not isinstance(editor, JogwheelDoubleSpinBox):
            return
        value = editor.value()
        steps = int((value * 1000) / STEP_DURATION_MS)
        model.setData(index, steps, Qt.ItemDataRole.EditRole)
