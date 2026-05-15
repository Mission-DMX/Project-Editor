"""Contains LayerConfigWidget."""

from __future__ import annotations

from logging import getLogger

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from model.filter_data.chaser_model import ChaserConfig, ChaserLayer, ChaserModel, ParameterType
from view.show_mode.editor.node_editor_widgets.chaser_editor._parameter_editors import (
    AbsoluteNumParameter,
    ColorParameter,
    PercentNumParameter,
)
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__name__)


class ChaserLayerConfigWidget(QWidget):
    """Widget to edit chaser layer setup instance.

    Widget provides a list of all layers, options to create and remove layers as well as an area allowing configuration
    of selected layer.

    """

    def __init__(self, parent_model: ChaserModel, parent: QWidget | None = None) -> None:
        """Initialize the widget."""
        super().__init__(parent)
        self._config: ChaserConfig | None = None
        self._model: ChaserModel = parent_model

        layout = QHBoxLayout()
        layer_layout = QVBoxLayout()
        self._layer_list: QListWidget = QListWidget(self)
        self._layer_list.itemSelectionChanged.connect(self._selected_layer_changed)
        self._layer_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layer_layout.addWidget(self._layer_list)
        self._add_layer_button = QPushButton("Add Layer")
        self._add_layer_button.setEnabled(False)
        self._add_layer_button.clicked.connect(self._add_layer_pressed)
        layer_layout.addWidget(self._add_layer_button)
        layout.addLayout(layer_layout)
        edit_layout = QVBoxLayout()
        self._remove_layer_button = QPushButton("Remove This Layer")
        self._remove_layer_button.setEnabled(False)
        self._remove_layer_button.clicked.connect(self._remove_layer_clicked)
        edit_layout.addWidget(self._remove_layer_button)
        self._layer_config_panel = QWidget()
        edit_layout.addWidget(self._layer_config_panel)
        layout.addLayout(edit_layout)
        self.setLayout(layout)

    @property
    def config(self) -> ChaserConfig | None:
        """Set or get the chaser configuration under edit."""
        return self._config

    @config.setter
    def config(self, value: ChaserConfig | None) -> None:
        self._config = value
        self._layer_list.clear()
        # TODO add layers using custom widget, use AnnotatedListWidgetItem and store layer as data
        self._add_layer_button.setEnabled(value is not None)

    def _construct_config_panel(self, layer: ChaserLayer) -> None:
        layout = self._layer_config_panel.layout()
        widget_to_delete = layout.takeAt(0)
        while widget_to_delete is not None:
            widget_to_delete = widget_to_delete.widget()
            widget_to_delete.deleteLater()
            widget_to_delete.setParent(None)
            widget_to_delete = layout.takeAt(0)
        del widget_to_delete
        if layer is None:
            self._remove_layer_button.setEnabled(False)
            return
        self._remove_layer_button.setEnabled(True)
        for i, parameter_template in enumerate(layer.parameter_templates):
            parameter_name, parameter_type, help_text = parameter_template
            layout.addItem(QSpacerItem(1, 16, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.ShrinkFlag))
            if parameter_type == ParameterType.COLOR:
                layout.addWidget(ColorParameter(parameter_name, help_text, i, layer, self._model))
            elif parameter_type == ParameterType.NUMBER_ABSOLUTE:
                layout.addWidget(AbsoluteNumParameter(parameter_name, help_text, i, layer, self._model))
            elif parameter_type == ParameterType.NUMBER_PERCENTAGE:
                layout.addWidget(PercentNumParameter(parameter_name, help_text, i, layer, self._model))
        layout.addItem(QSpacerItem(1, 16, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

    def _add_layer_pressed(self) -> None:
        pass  # TODO

    def _remove_layer_clicked(self) -> None:
        pass  # TODO

    def _selected_layer_changed(self) -> None:
        layer_item = self._layer_list.selectedItems()[0]
        if not isinstance(layer_item, AnnotatedListWidgetItem):
            logger.critical("Expected layer list item to be of type AnnotatedListWidgetItem.")
            return
        data = layer_item.annotated_data
        if data is None:
            return
        if not isinstance(data, ChaserLayer):
            logger.critical("Expected layer list item data to be of type ChaserLayer.")
            return
        self._construct_config_panel(data)
