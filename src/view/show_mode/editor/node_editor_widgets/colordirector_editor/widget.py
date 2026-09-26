"""Contains node editor widget."""

from __future__ import annotations

import os
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from controller.file.transmitting_to_fish import transmit_to_fish
from model.color_hsi import ColorHSI
from model.filter_data.transfer_function import TransferFunction
from model.media_assets.image import AbstractImageAsset
from model.media_assets.media_type import MediaType
from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter, ColorPreset
from utility import resource_path
from view.dialogs.asset_selection_dialog import AssetSelectionDialog
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.colordirector_editor._color_group_widget import ColorGroupWidget
from view.show_mode.editor.node_editor_widgets.colordirector_editor._recall_editor import RecallEditWidget
from view.show_mode.editor.node_editor_widgets.colordirector_editor.color_cell_delegate import ColorCellDelegate
from view.show_mode.editor.node_editor_widgets.colordirector_editor.fadein_time_cell_delegate import (
    FadeinTimeCellDelegate,
)
from view.show_mode.editor.node_editor_widgets.colordirector_editor.transfer_function_cell_delegate import (
    TransferFunctionCellDelegate,
)
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTableWidgetItem

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog

    from model import Filter
    from model.media_assets.asset import MediaAsset
    from view.show_mode.editor.nodes import FilterNode


logger = getLogger(__name__)
_IMAGE_ICON = QIcon(resource_path(os.path.join("resources", "icons", "media_image.svg")))


def _set_asset(asset: list[MediaAsset], preset: ColorPreset) -> None:
    if len(asset) == 0:
        preset.visualization_asset = None
        return
    selected_asset = asset[0]
    if isinstance(selected_asset, AbstractImageAsset):
        preset.visualization_asset = selected_asset
    else:
        preset.visualization_asset = None


class ColordirectorEditorWidget(NodeEditorFilterConfigWidget):
    """Configuration widget for Color Director.

    Provides a tab for the color groups, one for the presets and one for the recalls.

    """

    def __init__(self, model: Filter, parent: QWidget | None = None) -> None:
        """Initialize using color director model and optional parent."""
        super().__init__()
        if not isinstance(model, ColordirectorVFilter):
            raise TypeError("Color Director filter must be a ColordirectorVFilter.")
        self._in_preset_table_rebuild: bool = False
        self._model: ColordirectorVFilter = model
        self._widget = QTabWidget(parent)
        self._widget.setMinimumWidth(900)
        self._color_groups_tab = ColorGroupWidget(self._model, self._widget)
        self._widget.addTab(self._color_groups_tab, "Color Groups")

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
        self._preset_table.cellClicked.connect(self._preset_cell_clicked)
        self._preset_table.cellChanged.connect(self._preset_cell_edited)
        presets_layout.addWidget(self._preset_table)
        presets_tab.setLayout(presets_layout)
        self._widget.addTab(presets_tab, "Presets")

        recall_tab = RecallEditWidget(self._model, self._widget)
        self._color_groups_tab.groups_changed.connect(recall_tab.update_recall_table)
        self._widget.addTab(recall_tab, "Recalls")
        self._dialog: QDialog | None = None
        self._model.live_preview_mode = False

    @override
    def _get_configuration(self) -> dict[str, str]:
        self._model.serialize()
        return {}

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._reload_presets_table()

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        """Adopt the current model state without re-reading the stored configuration.

        Args:
            parameters: Ignored as all state is managed by the model directly.

        """
        return {}

    @override
    def _get_parameters(self) -> dict[str, str]:
        self._model.serialize()
        return self._model.initial_parameters

    @override
    def parent_opened(self) -> None:
        if len(self._model.output_groups) == 0:
            return
        self._dialog = YesNoDialog(
            self._widget, "Preview Mode", "Would you like to enable live editing?", self._enable_live_preview
        )
        self._dialog.setModal(True)

    def _reload_presets_table(self) -> None:
        self._load_default_colors_button.setEnabled(len(self._model.presets) == 0)
        self._in_preset_table_rebuild = True
        tw = self._preset_table
        tw.clear()
        row_sum = 0
        for preset in self._model.presets:
            row_sum += len(preset.colors)
        tw.setRowCount(row_sum)
        accent_color_maximum = self._model.get_accent_color_count()
        tw.setColumnCount(accent_color_maximum + 4)
        for i in range(accent_color_maximum + 4):
            tw.setColumnWidth(i, 125 if i > 0 else 175)
        for i in range(row_sum):
            tw.setRowHeight(i, 45)
        tw.setItemDelegateForColumn(1, FadeinTimeCellDelegate(tw))
        tw.setItemDelegateForColumn(2, TransferFunctionCellDelegate(tw))
        color_edit_delegate = ColorCellDelegate(tw)
        for i in range(accent_color_maximum):
            tw.setItemDelegateForColumn(i + 4, color_edit_delegate)
        offsets = 0
        for preset_index, preset in enumerate(self._model.presets):
            index_widget = AnnotatedTableWidgetItem(str(preset_index))
            index_widget.annotated_data = (preset_index, 0, -1)
            index_widget.setFlags(index_widget.flags() ^ Qt.ItemFlag.ItemIsEditable)
            last_index_item = index_widget
            initial_row = preset_index + offsets
            tw.setItem(preset_index + offsets, 0, index_widget)
            first_iteration = True
            step_index = -1
            for fade_in_time, transfer_function, accent_colors in preset.colors:
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

                add_accent_color_item = AnnotatedTableWidgetItem(" + ")
                add_accent_color_item.annotated_data = (preset_index, step_index, 2)
                tw.setItem(preset_index + offsets, 3, add_accent_color_item)
                add_accent_color_button = QPushButton("+")
                add_accent_color_button.setToolTip("Add accent color to step.")
                add_accent_color_button.clicked.connect(lambda _, ac=accent_colors: self._add_accent_color(ac))
                tw.setCellWidget(preset_index + offsets, 3, add_accent_color_button)

                for color_index, accent_color in enumerate(accent_colors):
                    accent_color_item = AnnotatedTableWidgetItem("   ")
                    accent_color_item.setToolTip(
                        f"H: {accent_color.hue} S: {accent_color.saturation} I: {accent_color.intensity}\n{
                            accent_color
                        }"
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
            asset_mgmt_button = QPushButton()
            asset_mgmt_button.setIcon(_IMAGE_ICON)
            asset_mgmt_button.clicked.connect(lambda _, p=preset: self._change_preset_asset_clicked(p))
            if len(preset.colors) < 2:
                add_step_layout.addWidget(asset_mgmt_button)
            else:
                first_index_item = tw.item(initial_row, 0)
                if first_index_item is None:
                    logger.error("Bug! Missing index item at %i:0 while rebuilding the presets table!", initial_row)
                    continue
                cell_widget = QWidget()
                asset_button_layout = QHBoxLayout()
                asset_button_layout.addWidget(QLabel(first_index_item.text()))
                asset_button_layout.addWidget(asset_mgmt_button)
                asset_mgmt_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                cell_widget.setLayout(asset_button_layout)
                first_index_item.setText("")
                tw.setCellWidget(first_index_item.row(), 0, cell_widget)
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
        annotated_data = item.annotated_data
        if annotated_data is None:
            logger.error("Bug! Preset Cell %i:%i does not provide position data!", row, column)
            return
        preset_index, step_index, property_index = annotated_data
        if property_index < 0:
            return
        if not (0 <= preset_index < len(self._model.presets)):
            logger.error("Bug! Preset Cell %i:%i provides invalid preset index (%i)!", row, column, preset_index)
            return
        preset = self._model.presets[preset_index]
        if not (0 <= step_index < len(preset.colors)):
            logger.error(
                "Bug! Preset Cell %i:%i provides invalid step (%i) for %i!", row, column, step_index, preset_index
            )
            return
        fade_in_time, tf, accent_colors = preset.colors[step_index]
        match property_index:
            case 0:
                # Fade in time
                edited_value = item.data(Qt.ItemDataRole.EditRole)
                if not isinstance(edited_value, int):
                    logger.error("Bug! Cell %i:%i received an invalid fade in time: %r!", row, column, edited_value)
                    return
                preset.colors[step_index] = (edited_value, tf, accent_colors)
                return
            case 1:
                edited_value = item.data(Qt.ItemDataRole.EditRole)
                if not isinstance(edited_value, TransferFunction):
                    logger.error("Bug! Cell %i:%i received invalid transfer function: %r!", row, column, edited_value)
                    return
                preset.colors[step_index] = (fade_in_time, edited_value, accent_colors)
                return
            case _:
                property_index -= 3
                if not (0 <= property_index < len(accent_colors)):
                    logger.error("Bug! cell %i:%i does not provide valid property: %i!", row, column, property_index)
                    return
                color = item.data(Qt.ItemDataRole.EditRole)
                if not isinstance(color, ColorHSI):
                    logger.error("Bug! Cell %i:%i received an invalid color: %r!", row, column, color)
                    return
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

    def _add_accent_color(self, accent_color_list: list[ColorHSI]) -> None:
        accent_color_list.append(ColorHSI(0.0, 0.0, 1.0))
        self._reload_presets_table()

    def _add_step_to_preset(self, preset: ColorPreset) -> None:
        preset.colors.append((0, TransferFunction.LINEAR, []))
        self._reload_presets_table()

    def _remove_last_step_from_preset(self, preset: ColorPreset) -> None:
        if len(preset.colors) == 0:
            return
        preset.colors.pop(-1)
        self._reload_presets_table()

    def _enable_live_preview(self) -> None:
        self._widget.setCurrentIndex(1)
        self._color_groups_tab.setEnabled(False)
        self._widget.setTabEnabled(0, False)
        self._model.live_preview_mode = True
        if not transmit_to_fish(self._model.scene.board_configuration, False):
            self._model.live_preview_mode = False
            self._color_groups_tab.setEnabled(True)
            self._widget.setTabEnabled(0, True)
            self._widget.setCurrentIndex(0)
            error_box = QMessageBox(self._widget)
            error_box.setWindowTitle("Live Preview Unavailable")
            error_box.setText("Live preview could not be enabled because the show could not be transmitted to fish.")
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.show()

    def _preset_cell_clicked(self, row: int, column: int) -> None:
        if self._model.live_preview_mode:
            item = self._preset_table.item(row, column)
            if not isinstance(item, AnnotatedTableWidgetItem):
                logger.error("Preview Cell %i:%i does not provide position data!", row, column)
                return
            annotated_data = item.annotated_data
            if annotated_data is None:
                logger.error("Preview Cell %i:%i does not provide position data!", row, column)
                return
            preset_index, step_index, property_index = annotated_data
            if property_index < 0:
                return
            if not (0 <= preset_index < len(self._model.presets)):
                logger.error("Preview Cell %i:%i provides invalid preset index (%i)!", row, column, preset_index)
                return
            preset = self._model.presets[preset_index]
            if not (0 <= step_index < len(preset.colors)):
                logger.error(
                    "Preview Cell %i:%i provides invalid step (%i) for %i!", row, column, step_index, preset_index
                )
                return
            _, _, accent_colors = preset.colors[step_index]
            self._model.apply_colors_on_preview_constants(accent_colors)

    @override
    def parent_closed(self, filter_node: FilterNode) -> None:
        if self._model.live_preview_mode:
            self._model.live_preview_mode = False
            if not transmit_to_fish(self._model.scene.board_configuration, False):
                logger.error("Failed to transmit the show to fish while disabling the live preview mode.")
        self._model.serialize()
        super().parent_closed(filter_node)

    def _change_preset_asset_clicked(self, preset: ColorPreset) -> None:
        self._dialog = AssetSelectionDialog(
            self._widget, preselected=preset.visualization_asset, allowed_types=[MediaType.IMAGE]
        )
        self._dialog.setModal(True)
        self._dialog.asset_selected.connect(lambda asset, p=preset: _set_asset(asset, p))
        self._dialog.show()
