from typing import override

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QLineEdit, QTableView

from model.media_assets.media_type import MediaType


class _AssetTableModel(QAbstractTableModel):
    """A table model providing the assets"""

    def __init__(self) -> None:
        super().__init__()

    def apply_filter(self, name: str, types: set[MediaType]) -> None:
        pass  # TODO

    @override
    def rowCount(self, parent=QModelIndex()):
        return 0  # TODO

    @override
    def columnCount(self, parent=QModelIndex()):
        return 5

    @override
    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole) -> None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return ("ID", "Type", "Name", "Preview", "Location")[section]
        else:
            return f"{section}"


class AssetSelectionWidget(QWidget):
    """
    Provide a sortable and searchable selection widget for assets.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self._type_button_bar = QToolBar(self)
        self._type_checkboxes: list[tuple[MediaType, QAction]] = []
        for asset_type in MediaType.all_values():
            type_action = QAction(self._type_button_bar)
            type_action.setText(asset_type.name)
            type_action.setCheckable(True)
            type_action.setChecked(True)
            type_action.toggled.connect(self._update_filter)
            self._type_button_bar.addAction(type_action)
            self._type_checkboxes.append((asset_type, type_action))
        layout.addWidget(self._type_button_bar)

        self._search_bar = QLineEdit(self)
        self._search_bar.textChanged.connect(self._update_filter)
        self._search_bar.setPlaceholderText("🔍")
        layout.addWidget(self._search_bar)

        self._asset_view = QTableView(self)
        self._model = _AssetTableModel()
        self._asset_view.setModel(self._model)
        layout.addWidget(self._asset_view)

        self.setLayout(layout)

    def _update_filter(self, _) -> None:
        selected_types = set()
        for asset_type, action in self._type_checkboxes:
            if action.isChecked():
                selected_types.add(asset_type)
        self._model.apply_filter(self._search_bar.text(), selected_types)
        self.update()