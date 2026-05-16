"""Provides Dialog that presents a layer to add."""

from __future__ import annotations

from logging import getLogger
from typing import override

from PySide6.QtGui import QImage, QMovie, QPixmap, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QVBoxLayout, QWidget

from model.filter_data.chaser_model import ChaserLayer, construct_chaser_layer
from view.show_mode.editor.node_editor_widgets.chaser_editor._layer_descriptions import LAYER_DESCRIPTION
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__name__)


class _LayerLabel(QWidget):
    def __init__(self, name: str, description: str, image: QImage | QMovie | None) -> None:
        super().__init__()
        layout = QHBoxLayout()
        label = QLabel()
        label.setFixedWidth(200)
        label.setFixedHeight(25)
        if image is None:
            label.setText("")
        elif isinstance(image, QMovie):
            label.setMovie(image)
            image.start()
        elif isinstance(image, QImage):
            label.setPixmap(QPixmap.fromImage(image))
        layout.addWidget(label)
        descr_layout = QVBoxLayout()
        descr_layout.addWidget(QLabel(name))
        descr_layout.addWidget(QLabel(description))
        layout.addLayout(descr_layout)
        self.setLayout(layout)


class AddLayerDialog(QDialog):
    """Dialog to add a layer to a chaser configuration.

    This dialog does not automatically the selected layer but provides it as a property.

    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.selected_layer: ChaserLayer | None = None
        layout = QVBoxLayout()
        self._layer_list_widget = QListWidget(self)
        self._layer_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for layer_key, layer_data in LAYER_DESCRIPTION.items():
            human_name, description, image = layer_data
            item = AnnotatedListWidgetItem(self._layer_list_widget)
            item.annotated_data = layer_key
            self._layer_list_widget.addItem(item)
            label = _LayerLabel(human_name, description, image)
            item.setSizeHint(label.sizeHint())
            self._layer_list_widget.setItemWidget(item, label)
        layout.addWidget(self._layer_list_widget)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, Qt.Orientation.Horizontal, self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.setModal(True)
        self.setWindowTitle("Add Layer")
        self.setMinimumSize(600, 800)

    @override
    def accept(self) -> None:
        selected_item = self._layer_list_widget.currentItem()
        if not isinstance(selected_item, AnnotatedListWidgetItem):
            logger.critical("Expected AnnotatedListWidgetItem.")
            return
        if not isinstance(selected_item.annotated_data, str):
            logger.critical("Expected str")
            return
        self.selected_layer = construct_chaser_layer(selected_item.annotated_data, [])
        super().accept()

    @override
    def reject(self) -> None:
        super().reject()
        self.close()
