from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractItemView, QLineEdit, QTableView, QToolBar, QVBoxLayout, QWidget

from model.media_assets.image import LocalImage
from model.media_assets.media_type import MediaType
from model.media_assets.registry import get_all_assets_of_type

if TYPE_CHECKING:
    from model.media_assets.asset import MediaAsset


class _AssetTableModel(QAbstractTableModel):
    """A table model providing the assets"""

    def __init__(self) -> None:
        super().__init__()
        self._selected_media_types: set[MediaType] = set()
        self._name_filter: str = ""
        self._filtered_asset_list: list[MediaAsset] = []

    def apply_filter(self, name: str, types: set[MediaType]) -> None:
        """Apply the filter parameters to the asset selection.
        Warning: this operation may be quite expensive. It is therefore better to wait for a filter to be entered
        completely prior to application.

        Args:
            name: If set to anything than an empty string, all assets needs to contain this in their name.
            types: The types of assets to show.
        """
        if types == self._selected_media_types and name == self._name_filter:
            return
        if len(name) < len(self._name_filter):
            self._filtered_asset_list.clear()
            self._selected_media_types.clear()
        types_to_add = types - self._selected_media_types
        types_to_remove = self._selected_media_types - types
        new_asset_list: list[MediaAsset] = [asset for asset in self._filtered_asset_list if
                                            ((asset.get_type() not in types_to_remove) and (name in asset.name))]
        for new_type in types_to_add:
            new_asset_list.extend([asset for asset in get_all_assets_of_type(new_type) if name in asset.name])
        changes_occured = new_asset_list != self._filtered_asset_list
        self._selected_media_types = types
        self._name_filter = name
        self._filtered_asset_list = new_asset_list
        if changes_occured:
            self.modelReset.emit()

    @override
    def rowCount(self, parent: QModelIndex | None) -> int:
        return len(self._filtered_asset_list)

    @override
    def columnCount(self, parent: QModelIndex | None) -> int:
        return 5

    @override
    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole) -> None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return ("ID", "Type", "Name", "Preview", "Location")[section]
        return f"{section}"

    @override
    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Any:
        asset = self._filtered_asset_list[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return asset.id
            if index.column() == 1:
                return asset.get_type().get_long_description()
            if index.column() == 2:
                return asset.name
            if index.column() == 3:
                return ""
            if index.column() == 4:
                return self._get_location_str(asset)
        elif role == Qt.ItemDataRole.EditRole:
            # TODO if column == 1 display drop down or dialog for internalizing
            if index.column() == 2:
                return asset.name
        elif role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 1:
                return asset.get_type().get_qt_hint_icon()
            if index.column() == 3:
                return asset.get_thumbnail()
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if index.column() < 2:
                return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
        elif role == Qt.ItemDataRole.ToolTipRole:
            if index.column() == 0:
                return asset.id
            if index.column() == 1:
                return f"{asset.get_type().get_long_description()} ({asset.__class__.__name__})"
            if index.column() == 4:
                return self._get_location_str(asset)
        return None

    def _get_location_str(self, asset: MediaAsset) -> str | None:
        """Get the media location of the provided asset (if any)."""
        if isinstance(asset, LocalImage):
            return asset.path
        return None

    @override
    def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole) -> bool:
        if index.column() != 2:
            return False
        asset = self._filtered_asset_list[index.row()]
        asset.name = str(value)
        return True

    @override
    def flags(self, index: QModelIndex, /) -> Qt.ItemFlag:
        parent_flag = super().flags(index)
        if index.isValid() and index.column() == 2:
            parent_flag |= Qt.ItemFlag.ItemIsEditable
        else:
            parent_flag &= ~Qt.ItemFlag.ItemIsEditable
        return parent_flag

    def asset_at(self, index: int) -> MediaAsset:
        """Get the asset at the provided index."""
        return self._filtered_asset_list[index]

    def get_row_indicies(self, assets: list[MediaAsset]) -> list[int]:
        """Get the indices of the rows whose assets are in the provided list."""
        return [index for index, asset in enumerate(self._filtered_asset_list) if asset in assets]


class AssetSelectionWidget(QWidget):
    """
    Provide a sortable and searchable selection widget for assets.
    """

    def __init__(self, parent: QWidget | None = None, allowed_types: list[MediaType] | None = None,
                 multiselection_allowed: bool = True) -> None:
        """
        Initialize the asset selection widget.

        Args:
            parent: The parent widget.
            allowed_types: The allowed asset types. Passing an empty list or None allows all types. Passing only one
            type disables the selection buttons.
            multiselection_allowed: Is the user allowed to select multiple rows?
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # TODO implement option to force assets of certain types
        self._type_button_bar = QToolBar(self)
        self._type_checkboxes: list[tuple[MediaType, QAction]] = []
        if allowed_types is None or allowed_types == []:
            allowed_types = MediaType.all_values()
        for asset_type in allowed_types:
            type_action = QAction(self._type_button_bar)
            type_action.setText(asset_type.name)
            type_action.setCheckable(True)
            type_action.setChecked(True)
            type_action.toggled.connect(self._update_filter)
            self._type_button_bar.addAction(type_action)
            self._type_checkboxes.append((asset_type, type_action))
        layout.addWidget(self._type_button_bar)
        self._type_button_bar.setVisible(len(self._type_checkboxes) > 1)

        self._search_bar = QLineEdit(self)
        self._search_bar.textChanged.connect(self._update_filter)
        self._search_bar.setPlaceholderText("🔍")
        layout.addWidget(self._search_bar)

        self._asset_view = QTableView(self)
        self._asset_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        if multiselection_allowed:
            self._asset_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        else:
            self._asset_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._model = _AssetTableModel()
        self._asset_view.setModel(self._model)
        layout.addWidget(self._asset_view)

        # TODO add timer to apply filter parameters after one second (experiment with 100ms and 500ms
        #  as well) of no changes
        self.setLayout(layout)
        self._update_filter()

    def _update_filter(self) -> None:
        selected_types: set[MediaType] = set()
        for asset_type, action in self._type_checkboxes:
            if action.isChecked():
                selected_types.add(asset_type)
        self._asset_view.setEnabled(False)
        self._model.apply_filter(self._search_bar.text(), selected_types)
        self._asset_view.setEnabled(True)
        self.update()

    @property
    def selected_asset(self) -> list[MediaAsset]:
        """Get or set the selected assets."""
        si = self._asset_view.selectionModel().selectedRows()
        asset_list: list[MediaAsset] = [self._model.asset_at(index.row()) for index in si]
        return asset_list

    @selected_asset.setter
    def selected_asset(self, selection: list[MediaAsset]) -> None:
        for index in self._model.get_row_indicies(selection):
            self._asset_view.selectRow(index)

