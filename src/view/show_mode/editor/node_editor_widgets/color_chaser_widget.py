"""Contains ColorChaserFilterConfigWidget, ChaserLayerConfigWidget and associated helper classes.

For the model, please have a look under model.filter_data.chaser_model


"""

from __future__ import annotations

import os
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtGui import QImage, QMovie, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget, QInputDialog, QMessageBox,
)

from model.events import EventFilter
from model.filter_data.chaser_model import ChaserConfig, ChaserModel
from utility import resource_path
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.node_editor_widgets.sequencer_editor.event_selection_dialog import EventSelectionDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog

    from model import Filter


logger = getLogger(__name__)


def _load_label_resource(path: str) -> QImage | QMovie | None:
    basename, ext = os.path.splitext(path)
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


class ChaserLayerConfigWidget(QWidget):
    """Widget to edit chaser layer setup instance.

    Widget provides a list of all layers, options to create and remove layers as well as an area allowing configuration
    of selected layer.

    """

    # TODO


class ColorChaserFilterConfigWidget(NodeEditorFilterConfigWidget):
    """Editor widget for color chaser."""

    def __init__(self, _filter: Filter) -> None:
        """Initialize config widget using instance of color chaser filter."""
        super().__init__()

        self._widget: QWidget = QWidget()
        self._input_dialog: QDialog | None = None
        self._live_updates_enabled = False
        self._model: ChaserModel | None = None
        self._filter: Filter = _filter

        top_layout = QVBoxLayout()
        general_settings_layout = QFormLayout()
        self._number_of_pixels_tb = QSpinBox()
        self._number_of_pixels_tb.setRange(1, 65535)
        general_settings_layout.addRow("Number of Pixels: ", self._number_of_pixels_tb)
        event_selection_layout = QHBoxLayout()
        self._event_label = QLabel("Time Mode")
        event_selection_layout.addWidget(self._event_label)
        event_selection_layout.addStretch()
        self._event_select_clear_button = QPushButton("Select Event")
        self._event_select_clear_button.clicked.connect(self._event_select_or_clear_clicked)
        event_selection_layout.addWidget(self._event_select_clear_button)
        general_settings_layout.addRow("Trigger Event: ", event_selection_layout)
        parameter_layout = QHBoxLayout()

        self._number_parameter_box = QGroupBox()
        self._number_parameter_list_widget = QListWidget()
        number_parameter_layout = QVBoxLayout()
        number_parameter_layout.addWidget(self._number_parameter_list_widget)
        self._add_number_parameter_button = QPushButton("Add Number Parameter")
        self._add_number_parameter_button.clicked.connect(self._add_number_parameter_pressed)
        number_parameter_layout.addWidget(self._add_number_parameter_button)
        self._delete_number_parameter_button = QPushButton("Delete Number Parameter")
        self._delete_number_parameter_button.clicked.connect(self._remove_number_parameter_pressed)
        number_parameter_layout.addWidget(self._delete_number_parameter_button)
        self._number_parameter_box.setLayout(number_parameter_layout)
        parameter_layout.addWidget(self._number_parameter_box)

        self._color_parameter_box = QGroupBox()
        self._color_parameter_list_widget = QListWidget()
        color_parameter_layout = QVBoxLayout()
        color_parameter_layout.addWidget(self._color_parameter_list_widget)
        self._add_color_parameter_button = QPushButton("Add Color Parameter")
        self._add_color_parameter_button.clicked.connect(self._add_color_parameter_pressed)
        color_parameter_layout.addWidget(self._add_color_parameter_button)
        self._delete_color_parameter_button = QPushButton("Delete Color Parameter")
        self._delete_color_parameter_button.clicked.connect(self._remove_color_parameter_pressed)
        color_parameter_layout.addWidget(self._delete_color_parameter_button)
        self._color_parameter_box.setLayout(color_parameter_layout)
        parameter_layout.addWidget(self._color_parameter_box)
        general_settings_layout.addRow("Parameters", parameter_layout)
        top_layout.addLayout(general_settings_layout)

        configlist_layer_slider = QSplitter(Qt.Orientation.Horizontal)
        configlist_container = QWidget()
        configlist_container_layout = QVBoxLayout()
        self._default_configuration_button = QLabel("TODO put button here selecting default configuration")
        configlist_container_layout.addWidget(self._default_configuration_button)
        self._additional_configurations_list = QListWidget()
        configlist_container_layout.addWidget(self._additional_configurations_list)
        add_del_configuration_layout = QHBoxLayout()
        self._add_configuration_button = QPushButton("Add Configuration")
        add_del_configuration_layout.addWidget(self._add_configuration_button)
        self._delete_configuration_button = QPushButton("Delete Configuration")
        add_del_configuration_layout.addWidget(self._delete_configuration_button)
        add_del_configuration_layout.addStretch()
        configlist_container_layout.addLayout(add_del_configuration_layout)
        configlist_container.setLayout(configlist_container_layout)
        configlist_layer_slider.addWidget(configlist_container)

        self._layer_config_widget = ChaserLayerConfigWidget()
        configlist_layer_slider.addWidget(self._layer_config_widget)

        top_layout.addWidget(configlist_layer_slider)
        self._widget.setLayout(top_layout)

    def _enable_live_updates(self) -> None:
        self._color_parameter_box.setEnabled(False)
        self._number_parameter_box.setEnabled(False)
        self._number_of_pixels_tb.setEnabled(False)
        self._event_select_clear_button.setEnabled(False)
        self._live_updates_enabled = True

    @override
    def _get_configuration(self) -> dict[str, str]:
        if self._model is None:
            return {}
        return self._model.get_as_configuration()

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._model = ChaserModel(conf)
        self._number_of_pixels_tb.setValue(self._model.number_of_pixels)
        self._load_number_parameter_list()
        self._load_color_parameter_list()
        if self._model.trigger_event is not None:
            sender, function, args = self._model.trigger_event
            self._event_label.setText(f"Trigger Event: {sender}:{function} -> {", ".join(args)}")
            self._event_select_clear_button.setText("Clear")
        # TODO populate default configuration
        # TODO populate presets

    def _load_number_parameter_list(self) -> None:
        if self._model is None:
            return
        for i, np in enumerate(self._model.number_parameters):
            item = AnnotatedListWidgetItem(self._number_parameter_list_widget)
            item.setText(np)
            item.annotated_data = i
            self._number_parameter_list_widget.addItem(item)

    def _load_color_parameter_list(self) -> None:
        if self._model is None:
            return
        for i, cp in enumerate(self._model.color_parameters):
            item = AnnotatedListWidgetItem(self._color_parameter_list_widget)
            item.setText(cp)
            item.annotated_data = i
            self._color_parameter_list_widget.addItem(item)

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        if self._model is None:
            logger.critical("Model should not be None at this point.")
            return {}
        default_config_str = parameters.get("config")
        if default_config_str is not None:
            self._model.default_config = ChaserConfig(default_config_str)
        return parameters

    @override
    def _get_parameters(self) -> dict[str, str]:
        model = self._model
        if model is None:
            return {}
        default_config = model.default_config
        if default_config is None:
            return {}
        return {
            "config": default_config.format_for_filter_str()
        }

    @override
    def parent_opened(self) -> None:
        self._live_updates_enabled = False
        # TODO only query this, if parameters are configured
        self._input_dialog = YesNoDialog(
            self.get_widget(), "Preview", "Would you like to switch to live preview?", self._enable_live_updates
        )

    def _event_select_or_clear_clicked(self) -> None:
        if self._model.trigger_event is None:
            self._input_dialog = EventSelectionDialog(self._widget)
            self._input_dialog.accepted.connect(self._event_selected_callback)
            self._input_dialog.show()
        else:
            self._event_label.setText("Time Mode")
            self._event_select_clear_button.setText("Select Event")
            self._model.trigger_event = None

    def _event_selected_callback(self) -> None:
        if not isinstance(self._input_dialog, EventSelectionDialog):
            logger.critical("Event selection dialog expected.")
            return
        sender, function, args = self._input_dialog.selected_event
        self._event_label.setText(f"Trigger Event: {sender}:{function} -> {args}")
        self._event_select_clear_button.setText("Clear")
        self._model.trigger_event = EventFilter(sender, function, [ord(c) for c in args])
        self._input_dialog.deleteLater()
        self._input_dialog = None

    def _add_number_parameter_pressed(self) -> None:
        self._input_dialog = QInputDialog(self._widget)
        self._input_dialog.setModal(True)
        self._input_dialog.setWindowTitle("Enter Name of Number Parameter")
        self._input_dialog.setTextValue("")
        self._input_dialog.setInputMode(QInputDialog.InputMode.TextInput)
        self._input_dialog.accepted.connect(self._add_number_parameter_dialog_callback)
        self._input_dialog.show()

    def _add_number_parameter_dialog_callback(self) -> None:
        if not isinstance(self._input_dialog, QInputDialog):
            return
        text = self._input_dialog.textValue()
        if not self._check_channel_input_name(text):
            return
        if self._model is None:
            return
        self._model.number_parameters.append(text)
        item = AnnotatedListWidgetItem(self._number_parameter_list_widget)
        item.setText(text)
        self._number_parameter_list_widget.addItem(item)

    def _check_channel_input_name(self, text: str) -> bool:
        if text in self._model.number_parameters or text in self._model.color_parameters or text in {"time", "time_scale"}:
            self._input_dialog = QMessageBox(QMessageBox.Icon.Critical, "Invalid parameter name",
                                             "An input channel with that name already exists.")
            self._input_dialog.setModal(True)
            self._input_dialog.show()
            return False
        if "|" in text or ":" in text or "," in text or ";" in text or "#" in text:
            self._input_dialog = QMessageBox(QMessageBox.Icon.Critical, "Invalid parameter name",
                                             "Input channels must not contain special characters.")
            self._input_dialog.setModal(True)
            self._input_dialog.show()
            return False
        return True

    def _remove_number_parameter_pressed(self) -> None:
        if self._model is None:
            return
        for selected_item in self._number_parameter_list_widget.selectedItems():
            self._model.number_parameters.remove(selected_item.text())
        self._number_parameter_list_widget.clear()
        self._load_number_parameter_list()

    def _add_color_parameter_pressed(self) -> None:
        self._input_dialog = QInputDialog(self._widget)
        self._input_dialog.setModal(True)
        self._input_dialog.setWindowTitle("Enter Name of Color Parameter")
        self._input_dialog.setTextValue("")
        self._input_dialog.setInputMode(QInputDialog.InputMode.TextInput)
        self._input_dialog.accepted.connect(self._add_color_parameter_dialog_callback)
        self._input_dialog.show()

    def _add_color_parameter_dialog_callback(self) -> None:
        if not isinstance(self._input_dialog, QInputDialog):
            return
        text = self._input_dialog.textValue()
        if not self._check_channel_input_name(text):
            return
        if self._model is None:
            return
        self._model.color_parameters.append(text)
        item = AnnotatedListWidgetItem(self._color_parameter_list_widget)
        item.setText(text)
        self._color_parameter_list_widget.addItem(item)

    def _remove_color_parameter_pressed(self) -> None:
        if self._model is None:
            return
        for selected_item in self._color_parameter_list_widget.selectedItems():
            self._model.color_parameters.remove(selected_item.text())
        self._color_parameter_list_widget.clear()
        self._load_color_parameter_list()
