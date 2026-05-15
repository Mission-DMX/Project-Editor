"""Contains LayerListItemWidget."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from model.filter_data.chaser_model import ChaserLayer
from view.show_mode.editor.node_editor_widgets.chaser_editor._layer_descriptions import LAYER_DESCRIPTION


class LayerListItemWidget(QWidget):
    """Label for displaying layer in list.

    This widget displays the human name and the variant data (if any).

    """

    def __init__(self, layer: ChaserLayer, parent: QWidget | None= None) -> None:
        """Initialize using provided layer."""
        super().__init__(parent)
        layout = QHBoxLayout()
        self._name_label = QLabel(LAYER_DESCRIPTION[layer.layer_identifier][0])
        layout.addSpacing(10)
        self._variant_label = QLabel(" ".join(layer.variant_data))
        layout.addWidget(self._variant_label)
        layout.addStretch()
        layout.addWidget(self._name_label)
        self.setLayout(layout)
