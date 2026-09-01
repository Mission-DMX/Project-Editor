"""Contains VariantEditor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QWidget

if TYPE_CHECKING:
    from model.filter_data.chaser_model import ChaserLayer


def _set_variant_data(index: int, layer: ChaserLayer, value: str) -> None:
    if value not in layer.variant_template[index]:
        raise ValueError(f"'{value}' is not a valid variant template at position {index}. "
                         f"Options: {layer.variant_template[index]}")
    layer.variant_data[index] = value


class VariantEditor(QWidget):
    """Widget to edit variant options of associated layer."""

    def __init__(self, layer: ChaserLayer, parent: QWidget | None = None) -> None:
        """Initialize the variant editor."""
        super().__init__(parent)
        layout = QHBoxLayout()
        for i, variant_temple in enumerate(layer.variant_template):
            cb = QComboBox()
            cb.setEditable(False)
            cb.addItems(variant_temple)
            cb.setCurrentText(layer.variant_data[i])
            cb.currentTextChanged.connect(lambda text, _layer=layer, _i=i: _set_variant_data(_i, _layer, text))
            layout.addWidget(cb)
        layout.addStretch()
        self.setLayout(layout)

