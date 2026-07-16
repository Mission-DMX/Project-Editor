"""Provide a dialog for selecting assets."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QVBoxLayout, QWidget
from qasync import QApplication

from model.media_assets.asset import MediaAsset
from view.utility_widgets.asset_selection_widget import AssetSelectionWidget

if TYPE_CHECKING:
    from model.media_assets.media_type import MediaType


class AssetSelectionDialog(QDialog):
    """A dialog for selecting assets."""

    asset_selected = Signal(MediaAsset)

    def __init__(self, parent: QWidget | None = None,
                 allowed_types: list[MediaType] | None = None,
                 preselected: MediaAsset | None = None,
                 multiselection_allowed: bool = False) -> None:
        """Initialize the dialog.

        Raises the asset_selected signal on user change.
        This dialog only allows selection of a single asset.

        Args:
            parent: The parent widget.
            preselected: A media asset that should be selected by default.
            allowed_types: A list of media types that the user is allowed to choose an asset from.
            multiselection_allowed: If True, the user may select multiple assets.

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

        self._asset_view = AssetSelectionWidget(self, allowed_types, multiselection_allowed)
        layout.addWidget(self._asset_view)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Horizontal, self
        )
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setLayout(layout)
        self.setMinimumSize(600, 800)

    @override
    def accept(self) -> None:
        self.asset_selected.emit(self._selection_widget.selected_asset)
        QApplication.processEvents()
        super().accept()
        self.close()

    def _clear(self) -> None:
        self._selection_widget.selected_asset = []

    @override
    def reject(self) -> None:
        super().reject()
        self.close()
