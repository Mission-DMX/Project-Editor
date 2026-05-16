"""Contains LayerConfigWidget."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from model.filter_data.chaser_model import ChaserConfig, ChaserLayer, ChaserModel, ParameterType
from view.show_mode.editor.node_editor_widgets.chaser_editor._layer_add_dialog import AddLayerDialog
from view.show_mode.editor.node_editor_widgets.chaser_editor._parameter_editors import (
    AbsoluteNumParameter,
    ColorParameter,
    PercentNumParameter,
)
from view.show_mode.editor.node_editor_widgets.chaser_editor._variant_editor import VariantEditor
from view.show_mode.editor.node_editor_widgets.chaser_editor.layer_list_item_widget import LayerListItemWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable


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
        self._apply_test_function: Callable[[ChaserConfig], None] | None = None
        self._dialog = None

        layout = QHBoxLayout()
        layer_layout = QVBoxLayout()
        self._layer_list: QListWidget = QListWidget(self)
        self._layer_list.itemSelectionChanged.connect(self._selected_layer_changed)
        self._layer_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layer_layout.addWidget(self._layer_list)
        edit_layout = QHBoxLayout()
        self._add_layer_button = QPushButton("Add Layer")
        self._add_layer_button.setEnabled(False)
        self._add_layer_button.clicked.connect(self._add_layer_pressed)
        edit_layout.addWidget(self._add_layer_button)
        layout.addLayout(layer_layout)
        self._remove_layer_button = QPushButton("Remove This Layer")
        self._remove_layer_button.setEnabled(False)
        self._remove_layer_button.clicked.connect(self._remove_layer_clicked)
        edit_layout.addWidget(self._remove_layer_button)
        edit_layout.addStretch()
        self._test_config_button = QPushButton("Test Configuration")
        self._test_config_button.setEnabled(False)
        self._test_config_button.clicked.connect(self._test_clicked)
        edit_layout.addWidget(self._test_config_button)
        self._layer_config_panel = QWidget()
        self._layer_config_panel.setMinimumWidth(400)
        self._layer_config_panel.setLayout(QVBoxLayout())
        layout.addWidget(self._layer_config_panel)
        layer_layout.addLayout(edit_layout)
        self.setLayout(layout)

    @property
    def config(self) -> ChaserConfig | None:
        """Set or get the chaser configuration under edit."""
        return self._config

    @config.setter
    def config(self, value: ChaserConfig | None) -> None:
        self._config = value
        self._layer_list.clear()
        if self._config is None:
            self._add_layer_button.setEnabled(False)
            return
        for layer in self._config.layers:
            self._add_layer_item(layer)
        self._add_layer_button.setEnabled(value is not None)
        self._test_config_button.setEnabled(value is not None and self._apply_test_function is not None)

    def set_test_method(self, test_function: Callable[[ChaserConfig], None] | None) -> None:
        """Set the function that should be executed if the test button is clicked."""
        self._apply_test_function = test_function

    @property
    def parent_model(self) -> ChaserModel | None:
        """Set or get the parent chaser model."""
        return self._model

    @parent_model.setter
    def parent_model(self, value: ChaserModel | None) -> None:
        self._model = value

    def _construct_config_panel(self, layer: ChaserLayer) -> None:
        layout = self._layer_config_panel.layout()
        if layout is not None:
            widget_to_delete = layout.takeAt(0)
            while widget_to_delete is not None:
                widget_to_delete = widget_to_delete.widget()
                if widget_to_delete is not None:
                    widget_to_delete.deleteLater()
                    widget_to_delete.setParent(None)
                widget_to_delete = layout.takeAt(0)
            del widget_to_delete
        if layer is None:
            self._remove_layer_button.setEnabled(False)
            return
        self._remove_layer_button.setEnabled(True)
        if len(layer.variant_template) > 0:
            layout.addWidget(VariantEditor(layer))
        for i, parameter_template in enumerate(layer.parameter_templates):
            parameter_name, parameter_type, help_text = parameter_template
            layout.addItem(QSpacerItem(1, 16, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding))
            if parameter_type == ParameterType.COLOR:
                layout.addWidget(ColorParameter(parameter_name, help_text, i, layer, self._model))
            elif parameter_type == ParameterType.NUMBER_ABSOLUTE:
                layout.addWidget(AbsoluteNumParameter(parameter_name, help_text, i, layer, self._model))
            elif parameter_type == ParameterType.NUMBER_PERCENTAGE:
                layout.addWidget(PercentNumParameter(parameter_name, help_text, i, layer, self._model))
        layout.addItem(QSpacerItem(1, 16, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

    def _add_layer_pressed(self) -> None:
        self._dialog = AddLayerDialog(self)
        self._dialog.accepted.connect(self._add_layer_selected)
        self._dialog.show()

    def _add_layer_selected(self) -> None:
        layer = self._dialog.selected_layer
        if layer is None:
            return
        self._config.layers.append(layer)
        self._add_layer_item(layer)

    def _add_layer_item(self, layer: ChaserLayer) -> None:
        item = AnnotatedListWidgetItem(self._layer_list)
        item.annotated_data = layer
        w = LayerListItemWidget(layer)
        item.setSizeHint(w.sizeHint())
        self._layer_list.addItem(item)
        self._layer_list.setItemWidget(item, w)


    def _remove_layer_clicked(self) -> None:
        self._dialog = YesNoDialog(
            self,
            "Are you sure?",
            "Do you really want to remove this layer?",
            self._remove_layer_confirmed,
            QMessageBox.Icon.Warning
        )
        self._dialog.show()

    def _remove_layer_confirmed(self) -> None:
        self._dialog.deleteLater()
        self._dialog = None
        selected_items = self._layer_list.selectedItems()
        indexes_to_remove: list[int] = []
        for item in selected_items:
            if not isinstance(item, AnnotatedListWidgetItem):
                continue
            if not isinstance(item.annotated_data, ChaserLayer):
                continue
            self._config.layers.remove(item.annotated_data)
            indexes_to_remove.append(self._layer_list.indexFromItem(item))
        indexes_to_remove.sort(reverse=True)
        for index in indexes_to_remove:
            self._layer_list.takeItem(index)

    def _selected_layer_changed(self) -> None:
        selected_items = self._layer_list.selectedItems()
        if len(selected_items) == 0:
            return
        layer_item = selected_items[0]
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

    def _test_clicked(self) -> None:
        if self._apply_test_function is not None and self._config is not None:
            self._apply_test_function(self._config)
