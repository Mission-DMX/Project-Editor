"""Contains ColorChaserFilterConfigWidget, ChaserLayerConfigWidget and associated helper classes.

For the model, please have a look under model.filter_data.chaser_model


"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, override

from PySide6.QtGui import QMovie, QImage
from PySide6.QtWidgets import QWidget

from model.filter_data.chaser_model import ChaserModel
from utility import resource_path
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog
    from model import Filter


LAYER_DESCRIPTION: dict[str, tuple[str, str, QImage | QMovie]] = {
    "plain_color": (
        "Plain Color",
        "This layer loads the provided color on the canvas using the mask value.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "plain_color.png"))),
    ),
    "rainbow": (
        "Rainbow",
        "Created a color gradient between two provided colors.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "rainbow.gif"))),
    ),
    "sprinkles": (
        "Sprinkles",
        "Draws random dots on the mask.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "sprinkles.gif"))),
    ),
    "dots": (
        "Dots",
        "Draws evenly distributed dots on the mask.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "dots.gif"))),
    ),
    "scale": (
        "Scale",
        "Draws a scale between two defined points on the mask.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "scale.gif"))),
    ),
    "scale_inv": (
        "Inverted Scale",
        "Draws a scale between two defined points on the mask.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "scale_inv.gif"))),
    ),
    "flat_mask": (
        "Flat Mask",
        "Sets the entire mask to a single constant value.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "flat_mask.png"))),
    ),
    "mask_shift": (
        "Mask Shift",
        "Shifts the mask after the specified number of milliseconds.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "mask_shift.gif"))),
    ),
    "color_shift": (
        "Color Shift",
        "Shifts pixel colors after the specified number of milliseconds.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "color_shift.gif"))),
    ),
    "trig": (
        "Trigonometric",
        "Updates the alpha mask using a trig function (sin, cos, tan) with specified parameters.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "trig.gif"))),
    ),
    "strobe": (
        "Strobe",
        "Enables and disables the alpha mask based on a BPM value.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "strobe.gif"))),
    ),
    "maskmod": (
        "Mask Modifier",
        "Modifies mask values (add, mul, div) over a selected width range.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "maskmod.png"))),
    ),
    "johnson": (
        "Johnson Counter",
        "Generates a Johnson counter effect on the mask (forward or reverse).",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "johnson.gif"))),
    ),
    "colormix": (
        "Color Mix",
        "Mixes two supplied colors and applies the result using the mask.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "colormix.png"))),
    ),
    "color_chanmod": (
        "Channel Set",
        "Sets a single channel (r, g, b, h, s, i) to the supplied numeric value.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "color_chanmod.png"))),
    ),
    "color_chancalc": (
        "Channel Calculation",
        "Modifies a channel (r, g, b, h, s, i) with an operation (add, sub, mult, div).",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "color_chancalc.png"))),
    ),
    "random_color": (
        "Random Color",
        "Generates N random colors and changes them every M ms.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "random_color.gif"))),
    ),
    "gaussian_blur": (
        "Gaussian Blur",
        "Applies a blur to pixels where the mask permits, using a size given in % of pixel width.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "gaussian_blur.png"))),
    ),
    "gaussian_curve_on_mask": (
        "Gaussian Curve on Mask",
        "Draws a Gaussian curve on the alpha mask (position, width, height).",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "gaussian_curve.png"))),
    ),
    "invert_color": (
        "Invert Color",
        "Inverts all color values on the canvas.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "invert_color.png"))),
    ),
    "invert_mask": (
        "Invert Mask",
        "Inverts the alpha mask.",
        QImage(resource_path(os.path.join("resources", "chaser_layer_help", "invert_mask.png"))),
    ),
    "close_to_center": (
        "Close to Center",
        "Pattern travels from edges toward the centre.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "close_to_center.gif"))),
    ),
    "open_from_center": (
        "Open from Center",
        "Pattern travels from the centre outward.",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "open_from_center.gif"))),
    ),
    "segwave": (
        "Segmented Wave",
        "Generates segmented waves on the mask (forward or reverse).",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "segwave.gif"))),
    ),
    "wave": (
        "Wave",
        "Generates a decaying wave on the mask (forward or reverse).",
        QMovie(resource_path(os.path.join("resources", "chaser_layer_help", "wave.gif"))),
    ),
}


class ColorChaserFilterConfigWidget(NodeEditorFilterConfigWidget):
    """Editor widget for color chaser."""

    def __init__(self, filter: Filter):
        super().__init__()

        self._widget: QWidget = QWidget()
        self._input_dialog: QDialog | None = None
        self._live_updates_enabled = False
        self._model: ChaserModel | None = None

    def _enable_live_updates(self):
        self._live_updates_enabled = True

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {}  # TODO

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._model = ChaserModel(conf)

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        pass  # TODO

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}  # TODO

    @override
    def parent_opened(self) -> None:
        self._live_updates_enabled = False
        self._input_dialog = YesNoDialog(
            self.get_widget(), "Preview", "Would you like to switch to live preview?", self._enable_live_updates
        )
