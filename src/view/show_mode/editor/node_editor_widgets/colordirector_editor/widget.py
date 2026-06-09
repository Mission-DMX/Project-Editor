"""Contains node editor widget."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from mypyc.irbuild.specialize import str_encode_fast_path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QTableWidget, QTabWidget, QVBoxLayout, QWidget

from controller.file.transmitting_to_fish import transmit_to_fish
from model.color_hsi import ColorHSI
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter, ColorPreset
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.colordirector_editor.color_cell_delegate import ColorCellDelegate
from view.show_mode.editor.node_editor_widgets.colordirector_editor.fadein_time_cell_delegate import (
    FadeinTimeCellDelegate,
)
from view.show_mode.editor.node_editor_widgets.colordirector_editor.transfer_function_cell_delegate import (
    TransferFunctionCellDelegate,
)
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTableWidgetItem

if TYPE_CHECKING:
    from model import Filter


logger = getLogger(__name__)

class ColordirectorEditorWidget(NodeEditorFilterConfigWidget):
    """Configuration widget for Color Director.

    Provides a tab for the color groups, one for the presets and one for the recalls.

    """

    def __init__(self, model: Filter, parent: QWidget | None = None) -> None:
        super().__init__()
        if not isinstance(model, ColordirectorVFilter):
            raise TypeError("Color Director filter must be a ColordirectorVFilter.")
        self._in_preset_table_rebuild: bool = False
        self._serialized_since_load: bool = False
        self._model: ColordirectorVFilter = model
        self._widget = QTabWidget(parent)
        self._widget.setMinimumWidth(800)
        color_groups_tab = QWidget(self._widget)
        color_groups_layout = QVBoxLayout()
        color_groups_layout.addWidget(QLabel("Color Groups: TreeWidget"))
        color_groups_tab.setLayout(color_groups_layout)
        self._widget.addTab(color_groups_tab, "Color Groups")

        presets_tab = QWidget(self._widget)
        presets_layout = QVBoxLayout()
        preset_buttons_layout = QHBoxLayout()
        self._load_default_colors_button = QPushButton("Load default colors")

        add_default_color_menu = QMenu(self._widget)
        add_default_color_menu.addAction("Add short default color list", self._load_default_colors_clicked_short)
        add_default_color_menu.addAction("Add long default color list", self._load_default_colors_clicked_long)
        self._load_default_colors_button.setMenu(add_default_color_menu)
        preset_buttons_layout.addWidget(self._load_default_colors_button)

        self._add_preset_button = QPushButton("Add preset")
        self._add_preset_button.clicked.connect(self._add_preset)
        preset_buttons_layout.addWidget(self._add_preset_button)

        preset_buttons_layout.addStretch()
        presets_layout.addLayout(preset_buttons_layout)
        self._preset_table = QTableWidget(presets_tab)
        self._preset_table.cellChanged.connect(self._preset_cell_edited)
        # TODO implement live preview mode: 1. Disable color group editing if in live preview. 2. Use Color constants
        #  for all outputs in group. 3. implement cellEntered signal to set output to current selected color preset
        #  4. Use a single color fader to dial in the color. On update: Calculate color distributions and apply them to
        #  constants. 5. Pressing record applies the current fader color to the current entered cell and updates the
        #  background color
        presets_layout.addWidget(self._preset_table)
        presets_tab.setLayout(presets_layout)
        self._widget.addTab(presets_tab, "Presets")

        recall_tab = QWidget(self._widget)
        recall_layout = QVBoxLayout()
        recall_layout.addWidget(QLabel("Recalls: TableWidget rows=recall columns=index"))
        recall_tab.setLayout(recall_layout)
        self._widget.addTab(recall_tab, "Recalls")

    @override
    def _get_configuration(self) -> dict[str, str]:
        if not self._serialized_since_load:
            self._model.serialize()
            self._serialized_since_load = True
        return {}

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._serialized_since_load = False
        self._reload_presets_table()

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        self._model.deserialize()
        self._serialized_since_load = False

    @override
    def _get_parameters(self) -> dict[str, str]:
        if not self._serialized_since_load:
            self._model.serialize()
            self._serialized_since_load = True
        return self._model.initial_parameters

    @override
    def parent_opened(self) -> None:
        super().parent_opened()
        # TODO update outputs of filter

    def _reload_presets_table(self) -> None:
        self._in_preset_table_rebuild = True
        tw = self._preset_table
        tw.clear()
        row_sum = 0
        for preset in self._model.presets:
            row_sum += len(preset.colors)
        tw.setRowCount(row_sum)
        ambient_color_maximum = self._model.get_ambient_color_count()
        tw.setColumnCount(ambient_color_maximum + 4)
        for i in range(ambient_color_maximum + 4):
            tw.setColumnWidth(i, 125)
        for i in range(row_sum):
            tw.setRowHeight(i, 45)
        tw.setItemDelegateForColumn(1, FadeinTimeCellDelegate(tw))
        tw.setItemDelegateForColumn(2, TransferFunctionCellDelegate(tw))
        color_edit_delegate = ColorCellDelegate(tw)
        for i in range(ambient_color_maximum):
            tw.setItemDelegateForColumn(i + 4, color_edit_delegate)
        offsets = 0
        for preset_index, preset in enumerate(self._model.presets):
            index_widget = AnnotatedTableWidgetItem(str(preset_index))
            index_widget.annotated_data = (preset_index, 0, -1)
            index_widget.setFlags(index_widget.flags() ^ Qt.ItemFlag.ItemIsEditable)
            last_index_item = index_widget
            tw.setItem(preset_index + offsets, 0, index_widget)
            first_iteration = True
            step_index = -1
            for fade_in_time, transfer_function, ambient_colors in preset.colors:
                if not first_iteration:
                    offsets += 1
                first_iteration = False
                step_index += 1

                fade_in_item = AnnotatedTableWidgetItem(str(fade_in_time))
                fade_in_item.annotated_data = (preset_index, step_index, 0)
                fade_in_item.setData(Qt.ItemDataRole.EditRole, fade_in_time)
                tw.setItem(preset_index + offsets, 1, fade_in_item)

                transfer_item = AnnotatedTableWidgetItem(transfer_function.value)
                transfer_item.annotated_data = (preset_index, step_index, 1)
                transfer_item.setData(Qt.ItemDataRole.EditRole, transfer_function)
                tw.setItem(preset_index + offsets, 2, transfer_item)

                add_accent_color_button = AnnotatedTableWidgetItem(" + ")
                add_accent_color_button.annotated_data = (preset_index, step_index, 2)
                tw.setItem(preset_index + offsets, 3, add_accent_color_button)
                add_accent_color_button = QPushButton("+")
                add_accent_color_button.setToolTip("Add accent color to step.")
                add_accent_color_button.clicked.connect(lambda _, ac=ambient_colors: self._add_accent_color(ac))
                tw.setCellWidget(preset_index + offsets, 3, add_accent_color_button)

                for color_index, accent_color in enumerate(ambient_colors):
                    accent_color_item = AnnotatedTableWidgetItem("   ")
                    accent_color_item.setToolTip(
                        f"H: {accent_color.hue} S: {accent_color.saturation} I: {accent_color.intensity
                        }\n{accent_color}"
                    )
                    accent_color_item.annotated_data = (preset_index, step_index, 3 + color_index)
                    accent_color_item.setBackground(accent_color.to_qt_color())
                    accent_color_item.setData(Qt.ItemDataRole.EditRole, accent_color)
                    tw.setItem(preset_index + offsets, 4 + color_index, accent_color_item)
            add_step_widget = QWidget()
            add_step_layout = QHBoxLayout()
            add_step_layout.addWidget(QLabel(str(preset_index)))
            add_step_layout.addStretch()
            add_step_button = QPushButton("↓")
            add_step_button.clicked.connect(lambda _, p=preset: self._add_step_to_preset(p))
            add_step_layout.addWidget(add_step_button)
            if len(preset.colors) > 1:
                remove_last_step_button = QPushButton("🗑")
                remove_last_step_button.clicked.connect(lambda _, p=preset: self._remove_last_step_from_preset(p))
                add_step_layout.addSpacing(10)
                add_step_layout.addWidget(remove_last_step_button)
            add_step_widget.setLayout(add_step_layout)
            tw.setCellWidget(preset_index + offsets, 0, add_step_widget)
            if len(preset.colors) < 2:
                last_index_item.setText("")
        self._in_preset_table_rebuild = False

    def _preset_cell_edited(self, row: int, column: int) -> None:
        if self._in_preset_table_rebuild:
            return
        item = self._preset_table.item(row, column)
        if not isinstance(item, AnnotatedTableWidgetItem):
            logger.error("Bug! Preset Cell %i:%i does not provide position data!", row, column)
            return
        preset_index, step_index, property_index = item.annotated_data
        if property_index < 0:
            return
        if not (0 <= preset_index < len(self._model.presets)):
            logger.error("Bug! Preset Cell %i:%i provides invalid preset index (%i)!",
                         row, column, preset_index)
            return
        preset = self._model.presets[preset_index]
        if not (0 <= step_index < len(preset.colors)):
            logger.error("Bug! Preset Cell %i:%i provides invalid step (%i) for %i!",
                         row, column, step_index, preset_index)
        fade_in_time, tf, accent_colors = preset.colors[step_index]
        match property_index:
            case -1:
                # Nothing to do for the index cell, this shouldn't happen anyway
                return
            case 0:
                # Fade in time
                fade_in_time = int(item.data(Qt.ItemDataRole.EditRole))
                preset.colors[step_index] = (fade_in_time, tf, accent_colors)
                return
            case 1:
                tf = item.data(Qt.ItemDataRole.EditRole)
                preset.colors[step_index] = (fade_in_time, tf, accent_colors)
                return
            case _:
                property_index -= 3
                if not(0 < property_index < len(accent_colors)):
                    logger.error("Bug! cell %i:%i does not provide valid property: %i!",
                                 row, column, property_index)
                color = item.data(Qt.ItemDataRole.EditRole)
                if not isinstance(color, ColorHSI):
                    raise ValueError("Received invalid color data.")
                accent_colors[property_index] = color
                item.setBackground(color.to_qt_color())
                return

    def _load_default_colors_clicked_short(self) -> None:
        self._model.populate_presets_with_initial_data(True)
        self._reload_presets_table()

    def _load_default_colors_clicked_long(self) -> None:
        self._model.populate_presets_with_initial_data(False)
        self._reload_presets_table()

    def _add_preset(self) -> None:
        self._model.presets.append(ColorPreset())
        self._reload_presets_table()

    def _add_accent_color(self, ambient_color_list: list[ColorHSI]) -> None:
        ambient_color_list.append(ColorHSI(0.0, 0.0, 1.0))
        self._reload_presets_table()

    def _add_step_to_preset(self, preset: ColorPreset) -> None:
        preset.colors.append((0, TransferFunction.LINEAR, []))
        # FIXME funny things happen with the data of following presets
        self._reload_presets_table()

    def _remove_last_step_from_preset(self, preset: ColorPreset) -> None:
        if len(preset.colors) == 0:
            return
        preset.colors.pop(-1)
        self._reload_presets_table()
