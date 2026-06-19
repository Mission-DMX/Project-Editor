"""Contains AssetSelectionDialog."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QVBoxLayout, QWidget

from model.media_assets.asset import MediaAsset
from view.utility_widgets.asset_selection_widget import AssetSelectionWidget

if TYPE_CHECKING:
    from model.media_assets.media_type import MediaType


class AssetSelectionDialog(QDialog):
    """Dialog to select an asset."""

    asset_selected = Signal(MediaAsset)

    def __init__(self, parent: QWidget,
                 preselected: MediaAsset | None = None,
                 allowed_types: list[MediaType] | None = None) -> None:
        """Initialize AssetSelectionDialog.

        Raises the asset_selected signal on user change.
        THis dialog only allows selection of a single asset.

        Args:
            parent: The parent widget.
            preselected: A media asset that should be selected by default.
            allowed_types: A list of media types that the user is allowed to choose an asset from.

        """
        super().__init__(parent)
        self._selection_widget = AssetSelectionWidget(self,
                                                      allowed_types=allowed_types if allowed_types is not None else [],
                                                      multiselection_allowed=False)
        self._selection_widget.selected_asset = [preselected] if preselected is not None else []
        self._clear_selection_button = QPushButton("Clear Selection")
        self._clear_selection_button.clicked.connect(self._clear)
        layout = QVBoxLayout()
        layout.addWidget(self._clear_selection_button)
        layout.addWidget(self._selection_widget)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        self._button_box.accepted.connect(self._accept)
        self._button_box.rejected.connect(self.close)
        layout.addWidget(self._button_box)
        self.setLayout(layout)
        self.setMinimumSize(600, 800)

    def _clear(self) -> None:
        self._selection_widget.selected_asset = []

    def _accept(self) -> None:
        selected_assets = self._selection_widget.selected_asset
        if len(selected_assets) > 0:
            self.asset_selected.emit(selected_assets[0])
        else:
            self.asset_selected.emit(None)
        self.accept()
