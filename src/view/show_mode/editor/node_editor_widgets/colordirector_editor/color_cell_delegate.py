"""Contains color cell item widget delegate."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDoubleSpinBox, QHBoxLayout, QLabel, QStyledItemDelegate, QWidget

from model.color_hsi import ColorHSI
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorLabel

if TYPE_CHECKING:
    from PySide6.QtCore import QAbstractItemModel, QLocale, QModelIndex
    from PySide6.QtWidgets import QStyleOptionViewItem


class ColorEditWidget(QWidget):
    """Widget allowing editing of color."""

    def __init__(self, parent: QWidget) -> None:
        """Initialize using parent."""
        super().__init__(parent)
        layout = QHBoxLayout()
        self._color_label = ColorLabel()
        self._color_label.setFixedSize(16, 16)
        layout.addWidget(self._color_label)
        self._hue_edit = QDoubleSpinBox()
        self._hue_edit.setRange(0, 359.99)
        self._hue_edit.valueChanged.connect(self._update_color)
        layout.addWidget(self._hue_edit)
        self._sat_edit = QDoubleSpinBox()
        self._sat_edit.valueChanged.connect(self._update_color)
        self._sat_edit.setRange(0, 1)
        layout.addWidget(self._sat_edit)
        self._val_edit = QDoubleSpinBox()
        self._val_edit.valueChanged.connect(self._update_color)
        self._val_edit.setRange(0, 1)
        layout.addWidget(self._val_edit)
        self.setLayout(layout)

    def set_color(self, color: ColorHSI) -> None:
        """Set the color of the edit widget."""
        self._hue_edit.setValue(color.hue)
        self._sat_edit.setValue(color.saturation)
        self._val_edit.setValue(color.intensity)

    def get_color(self) -> ColorHSI:
        """Get the color of the edit widget."""
        return ColorHSI(self._hue_edit.value(), self._sat_edit.value(), self._val_edit.value())

    def _update_color(self) -> None:
        self._color_label.set_hsi(self._hue_edit.value(), self._sat_edit.value(), self._val_edit.value())


class ColorCellDelegate(QStyledItemDelegate):
    """Color cell item delegate.

    Item delegate to allow editing of color cells. Displaying is taken care of by table widget background color.

    """

    @override
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex, /) -> QWidget:
        if index.data(Qt.ItemDataRole.EditRole) is None:
            return QLabel("No Color.", parent)
        return ColorEditWidget(parent)

    @override
    def setEditorData(self, editor: QLabel | ColorEditWidget, index: QModelIndex, /) -> None:
        if isinstance(editor, QLabel):
            return
        data = index.data(Qt.ItemDataRole.EditRole)
        if data is None:
            return
        editor.set_color(data)

    @override
    def setModelData(self, editor: QLabel | ColorEditWidget, model: QAbstractItemModel, index: QModelIndex, /) -> None:
        if isinstance(editor, QLabel):
            return
        color = editor.get_color()
        model.setData(index, color, Qt.ItemDataRole.EditRole)
