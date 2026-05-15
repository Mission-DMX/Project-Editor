"""Contains layer descriptions to be used in add layer dialog."""

import os
from logging import getLogger

from PySide6.QtGui import QImage, QMovie

from utility import resource_path

logger = getLogger(__name__)

def _load_label_resource(path: str) -> QImage | QMovie | None:
    _, ext = os.path.splitext(path)
    if not os.path.exists(path):
        logger.critical("Failed to load label resource: File %s not found.", path)
        return None
    if ext.lower() == ".png":
        return QImage(path)
    return QMovie(path)


LAYER_DESCRIPTION: dict[str, tuple[str, str, QImage | QMovie | None]] = {
    "plain_color": (
        "Plain Color",
        "This layer loads the provided color on the canvas using the mask value.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "plain_color.png"))),
    ),
    "rainbow": (
        "Rainbow",
        "Created a color gradient between two provided colors.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "rainbow.gif"))),
    ),
    "sprinkles": (
        "Sprinkles",
        "Draws random dots on the mask.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "sprinkles.gif"))),
    ),
    "dots": (
        "Dots",
        "Draws evenly distributed dots on the mask.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "dots.gif"))),
    ),
    "scale": (
        "Scale",
        "Draws a scale between two defined points on the mask.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "scale.gif"))),
    ),
    "scale_inv": (
        "Inverted Scale",
        "Draws a scale between two defined points on the mask.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "scale_inv.gif"))),
    ),
    "flat_mask": (
        "Flat Mask",
        "Sets the entire mask to a single constant value.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "flat_mask.png"))),
    ),
    "mask_shift": (
        "Mask Shift",
        "Shifts the mask after the specified number of milliseconds.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "mask_shift.gif"))),
    ),
    "color_shift": (
        "Color Shift",
        "Shifts pixel colors after the specified number of milliseconds.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "color_shift.gif"))),
    ),
    "trig": (
        "Trigonometric",
        "Updates the alpha mask using a trig function (sin, cos, tan) with specified parameters.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "trig.gif"))),
    ),
    "strobe": (
        "Strobe",
        "Enables and disables the alpha mask based on a BPM value.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "strobe.gif"))),
    ),
    "maskmod": (
        "Mask Modifier",
        "Modifies mask values (add, mul, div) over a selected width range.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "maskmod.png"))),
    ),
    "johnson": (
        "Johnson Counter",
        "Generates a Johnson counter effect on the mask (forward or reverse).",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "johnson.gif"))),
    ),
    "colormix": (
        "Color Mix",
        "Mixes two supplied colors and applies the result using the mask.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "colormix.png"))),
    ),
    "color_chanmod": (
        "Channel Set",
        "Sets a single channel (r, g, b, h, s, i) to the supplied numeric value.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "color_chanmod.png"))),
    ),
    "color_chancalc": (
        "Channel Calculation",
        "Modifies a channel (r, g, b, h, s, i) with an operation (add, sub, mult, div).",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "color_chancalc.png"))),
    ),
    "random_color": (
        "Random Color",
        "Generates N random colors and changes them every M ms.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "random_color.gif"))),
    ),
    "gaussian_blur": (
        "Gaussian Blur",
        "Applies a blur to pixels where the mask permits, using a size given in % of pixel width.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "gaussian_blur.png"))),
    ),
    "gaussian_curve_on_mask": (
        "Gaussian Curve on Mask",
        "Draws a Gaussian curve on the alpha mask (position, width, height).",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "gaussian_curve.png"))),
    ),
    "invert_color": (
        "Invert Color",
        "Inverts all color values on the canvas.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "invert_color.png"))),
    ),
    "invert_mask": (
        "Invert Mask",
        "Inverts the alpha mask.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "invert_mask.png"))),
    ),
    "close_to_center": (
        "Close to Center",
        "Pattern travels from edges toward the centre.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "close_to_center.gif"))),
    ),
    "open_from_center": (
        "Open from Center",
        "Pattern travels from the centre outward.",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "open_from_center.gif"))),
    ),
    "segwave": (
        "Segmented Wave",
        "Generates segmented waves on the mask (forward or reverse).",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "segwave.gif"))),
    ),
    "wave": (
        "Wave",
        "Generates a decaying wave on the mask (forward or reverse).",
        _load_label_resource(resource_path(os.path.join("resources", "chaser_layer_help", "wave.gif"))),
    ),
}
