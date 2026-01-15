"""Provide a dialog for selecting assets."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QWidget
from qasync import QApplication

from model.media_assets.asset import MediaAsset
from view.utility_widgets.asset_selection_widget import AssetSelectionWidget

if TYPE_CHECKING:
    from model.media_assets.media_type import MediaType


class AssetSelectionDialog(QDialog):
    """A dialog for selecting assets."""

    asset_selected: Signal = Signal(MediaAsset)

    def __init__(self, parent: QWidget | None = None,
                 allowed_types: list[MediaType] | None = None, multiselection_allowed: bool = False) -> None:
        """Initialize the dialog."""
        super().__init__(parent)
        layout = QVBoxLayout()

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

    @override
    def accept(self) -> None:
        self.asset_selected.emit(self._asset_view.selected_asset)
        QApplication.processEvents()
        super().accept()
        self.close()

    @override
    def reject(self) -> None:
        super().reject()
        self.close()
