"""Contains the asset management dialog."""

from __future__ import annotations

import os

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox, QToolBar, QVBoxLayout, QWidget

from controller.utils.process_notifications import ProcessNotifier, get_process_notifier
from model.media_assets.image import LocalImage
from model.media_assets.media_type import MediaType
from view.utility_widgets.asset_selection_widget import AssetSelectionWidget

_SUPPORTED_FILE_ENDINGS: dict[MediaType, list[str]] = {
    MediaType.TEXT: [".txt"],
    MediaType.IMAGE: [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".pbm", ".pgm", ".ppm", ".xbm", ".xpm"],
    MediaType.VIDEO: [".mp4"],
    MediaType.AUDIO: [".wav", ".mp3", ".flac"],
    MediaType.MODEL_3D: [".stl", ".obj"]
}


class AssetManagementDialog(QDialog):
    """Provide a GUI method to manage assets."""

    def __init__(self, parent: QWidget | None = None, show_file_path: str | None = None) -> None:
        """Initialize the asset management dialog."""
        super().__init__(parent)
        layout = QVBoxLayout()

        self._action_button_group = QToolBar()

        self._load_asset_file = QAction()
        self._load_asset_file.setIcon(QIcon.fromTheme("document-open"))
        self._load_asset_file.setText("Load asset from file")
        self._load_asset_file.triggered.connect(self._open_file)
        self._action_button_group.addAction(self._load_asset_file)
        self._delete_selected_asset_action = QAction()
        self._delete_selected_asset_action.setIcon(QIcon.fromTheme("edit-delete"))
        self._delete_selected_asset_action.setText("Delete selected asset")
        self._delete_selected_asset_action.triggered.connect(self._delete_selected_asset)
        self._delete_selected_asset_action.setEnabled(False)
        self._action_button_group.addAction(self._delete_selected_asset_action)

        layout.addWidget(self._action_button_group)

        self._asset_display = AssetSelectionWidget(self, multiselection_allowed=True)
        layout.addWidget(self._asset_display)

        self._close_button_group = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._close_button_group.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.close)
        layout.addWidget(self._close_button_group)

        self.setLayout(layout)
        self.setModal(True)
        self._dialog: QFileDialog | None = None
        self._show_file_path = show_file_path if show_file_path is not None else ""
        self.setMinimumWidth(800)
        self._asset_display.asset_selection_changed.connect(self._selected_asset_changed)

    def _open_file(self) -> None:
        self._dialog = QFileDialog(self, "Open file")
        self._dialog.setModal(True)
        self._dialog.setNameFilters(
            [f"{k.get_long_description()} ({" ".join(f"*{va}" for va in v)})"
             for k, v in _SUPPORTED_FILE_ENDINGS.items()]
        )
        self._dialog.setDefaultSuffix(".jpg")
        self._dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self._dialog.setDirectory(os.path.expanduser("~") if self._show_file_path is None else self._show_file_path)
        self._dialog.filesSelected.connect(self._process_loading_files)
        self._dialog.open()

    def _process_loading_files(self, list_of_files: list[str]) -> None:
        self._dialog.close()
        if len(list_of_files) == 0:
            return
        accumulated_errors = ""
        pn = get_process_notifier("Asset Loading", len(list_of_files))
        for file_path in list_of_files:
            pn.current_step_description = f"Loading Asset from {file_path}"
            extension = os.path.splitext(file_path)[1]
            try:
                if extension in _SUPPORTED_FILE_ENDINGS[MediaType.IMAGE]:
                    LocalImage(file_path, show_file_path=self._show_file_path)
                else:
                    accumulated_errors += f"Unable to load asset from {file_path}: extension {extension} unknown.\n"
            except Exception as e:
                accumulated_errors += f"Unable to load asset from {file_path}: {e}\n"
            pn.current_step_number += 1
        self._asset_display.reload_model()
        pn.close()
        if len(accumulated_errors) > 0:
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Loading Assets Failed",
                                  "Errors occurred during asset loading:", parent=self,
                                  detailedText=accumulated_errors)
            msg_box.show()
            self._dialog = msg_box

    def _selected_asset_changed(self) -> None:
        self._delete_selected_asset_action.setEnabled(len(self._asset_display.selected_asset) > 0)

    def _delete_selected_asset(self) -> None:
        for asset in self._asset_display.selected_asset:
            asset.unregister()
        self._asset_display.reload_model()
