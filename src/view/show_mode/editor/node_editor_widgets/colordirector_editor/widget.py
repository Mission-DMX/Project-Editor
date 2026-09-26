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
    from model import Filter
    from model.media_assets.asset import MediaAsset
    from view.show_mode.editor.nodes import FilterNode


logger = getLogger(__name__)
_IMAGE_ICON = QIcon(resource_path(os.path.join("resources", "icons", "media_image.svg")))

_PRESET_INDEX_COLUMN = 0
"""Table column displaying the preset index, the preset management buttons and the visualization asset."""

_FADE_IN_TIME_COLUMN = 1
"""Table column displaying the fade in time of a preset step."""

_TRANSFER_FUNCTION_COLUMN = 2
"""Table column displaying the transfer function of a preset step."""

_ADD_ACCENT_COLOR_COLUMN = 3
"""Table column providing the button adding another accent color to a preset step."""

_ACCENT_COLOR_COLUMN_OFFSET = 4
"""Table column index of the first accent color column: Further accent colors follow consecutively."""

_PRESET_LEVEL_PROPERTY = -1
"""Annotated property index of the preset index item: It belongs to the preset instead of one of its steps."""

_FADE_IN_TIME_PROPERTY = 0
"""Annotated property index identifying the fade in time of a preset step."""

_TRANSFER_FUNCTION_PROPERTY = 1
"""Annotated property index identifying the transfer function of a preset step."""

_ADD_ACCENT_COLOR_PROPERTY = 2
"""Annotated property index of the button adding another accent color to a preset step."""

_ACCENT_COLOR_PROPERTY_OFFSET = 3
"""Annotated property index of the first accent color of a preset step: Further accent colors follow using
consecutive indices."""


def _set_asset(asset: list[MediaAsset], preset: ColorPreset) -> None:
    """Set the visualization asset of the preset to the first selected image asset.

    The visualization asset is cleared if the selection is empty or does not contain an image asset.

    Args:
        asset: The assets selected within the asset selection dialog.
        preset: The preset whose visualization asset is set.

    """
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

        self._live_preview_button = QPushButton("Live Preview")
        self._live_preview_button.setCheckable(True)
        self._live_preview_button.setToolTip(
            "Toggle the live preview mode. While it is active, color groups can not be edited."
        )
        self._live_preview_button.clicked.connect(self._live_preview_button_clicked)
        preset_buttons_layout.addWidget(self._live_preview_button)

        preset_buttons_layout.addStretch()
        presets_layout.addLayout(preset_buttons_layout)
        self._preset_table = QTableWidget(presets_tab)
        self._preset_table.cellClicked.connect(self._preset_cell_clicked)
        self._preset_table.cellChanged.connect(self._preset_cell_edited)
        presets_layout.addWidget(self._preset_table)
        presets_tab.setLayout(presets_layout)
        self._widget.addTab(presets_tab, "Presets")

        self._recall_tab = RecallEditWidget(self._model, self._widget)
        self._color_groups_tab.groups_changed.connect(self._recall_tab.update_recall_table)
        self._widget.addTab(self._recall_tab, "Recalls")
        self._preview_dialog: YesNoDialog | None = None
        self._asset_dialog: AssetSelectionDialog | None = None
        self._apply_live_preview_ui_state()

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
        # ask only once per session per filter: the live preview can also be toggled using the
        # "Live Preview" button of the presets tab
        if self._model.live_preview_mode or self._model.live_preview_prompted:
            return
        self._model.live_preview_prompted = True
        if self._preview_dialog is not None:
            self._preview_dialog.deleteLater()
        self._preview_dialog = YesNoDialog(
            self._widget, "Preview Mode", "Would you like to enable live editing?", self._enable_live_preview
        )
        self._preview_dialog.setModal(True)

    def _reload_presets_table(self) -> None:
        """Rebuild the presets table from the current model state."""
        self._load_default_colors_button.setEnabled(len(self._model.presets) == 0)
        self._in_preset_table_rebuild = True
        try:
            self._prepare_preset_table_layout()
            row_offset = 0
            for preset_index, preset in enumerate(self._model.presets):
                row_offset += self._add_preset_to_table(preset_index, preset, row_offset)
        finally:
            self._in_preset_table_rebuild = False

    def _prepare_preset_table_layout(self) -> None:
        """Clear the presets table and prepare its layout, sizes and item delegates."""
        tw = self._preset_table
        tw.clear()
        row_sum = 0
        for preset in self._model.presets:
            row_sum += max(len(preset.colors), 1)
        tw.setRowCount(row_sum)
        accent_color_maximum = self._model.get_accent_color_count()
        column_count = accent_color_maximum + _ACCENT_COLOR_COLUMN_OFFSET
        tw.setColumnCount(column_count)
        for i in range(column_count):
            tw.setColumnWidth(i, 125 if i > _PRESET_INDEX_COLUMN else 175)
        for i in range(row_sum):
            tw.setRowHeight(i, 45)
        tw.setItemDelegateForColumn(_FADE_IN_TIME_COLUMN, FadeinTimeCellDelegate(tw))
        tw.setItemDelegateForColumn(_TRANSFER_FUNCTION_COLUMN, TransferFunctionCellDelegate(tw))
        color_edit_delegate = ColorCellDelegate(tw)
        for i in range(accent_color_maximum):
            tw.setItemDelegateForColumn(i + _ACCENT_COLOR_COLUMN_OFFSET, color_edit_delegate)

    def _add_preset_to_table(self, preset_index: int, preset: ColorPreset, start_row: int) -> int:
        """Populate the table rows used by a single color preset.

        Every step of the preset occupies one row. Presets without steps occupy a single row without step
        content. The preset index and the buttons managing the preset are placed within the first and the last
        row used by the preset.

        Args:
            preset_index: The index of the preset within the model.
            preset: The preset to populate the table rows for.
            start_row: The first table row used by the preset.

        Returns:
            The number of table rows used by the preset.

        """
        tw = self._preset_table
        index_item = AnnotatedTableWidgetItem(str(preset_index))
        index_item.annotated_data = (preset_index, 0, _PRESET_LEVEL_PROPERTY)
        index_item.setFlags(index_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        tw.setItem(start_row, _PRESET_INDEX_COLUMN, index_item)
        for step_index, (fade_in_time, transfer_function, accent_colors) in enumerate(preset.colors):
            self._add_step_to_table(
                preset_index, step_index, start_row + step_index, fade_in_time, transfer_function, accent_colors
            )
        used_rows = max(len(preset.colors), 1)
        self._add_preset_buttons_to_table(preset_index, preset, index_item, start_row, start_row + used_rows - 1)
        return used_rows

    def _add_step_to_table(
        self,
        preset_index: int,
        step_index: int,
        row: int,
        fade_in_time: int,
        transfer_function: TransferFunction,
        accent_colors: list[ColorHSI],
    ) -> None:
        """Add the table row displaying a single preset step.

        Args:
            preset_index: The index of the preset the step belongs to.
            step_index: The index of the step within the preset.
            row: The table row to display the step in.
            fade_in_time: The fade in time of the step in steps.
            transfer_function: The transfer function of the step.
            accent_colors: The accent colors of the step.

        """
        tw = self._preset_table
        fade_in_item = AnnotatedTableWidgetItem(str(fade_in_time))
        fade_in_item.annotated_data = (preset_index, step_index, _FADE_IN_TIME_PROPERTY)
        fade_in_item.setData(Qt.ItemDataRole.EditRole, fade_in_time)
        tw.setItem(row, _FADE_IN_TIME_COLUMN, fade_in_item)

        transfer_item = AnnotatedTableWidgetItem(transfer_function.value)
        transfer_item.annotated_data = (preset_index, step_index, _TRANSFER_FUNCTION_PROPERTY)
        transfer_item.setData(Qt.ItemDataRole.EditRole, transfer_function)
        tw.setItem(row, _TRANSFER_FUNCTION_COLUMN, transfer_item)

        add_accent_color_item = AnnotatedTableWidgetItem(" + ")
        add_accent_color_item.annotated_data = (preset_index, step_index, _ADD_ACCENT_COLOR_PROPERTY)
        add_accent_color_item.setFlags(add_accent_color_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        tw.setItem(row, _ADD_ACCENT_COLOR_COLUMN, add_accent_color_item)
        add_accent_color_button = QPushButton("+")
        add_accent_color_button.setToolTip("Add accent color to step.")
        add_accent_color_button.clicked.connect(lambda _, ac=accent_colors: self._add_accent_color(ac))
        tw.setCellWidget(row, _ADD_ACCENT_COLOR_COLUMN, add_accent_color_button)

        for color_index, accent_color in enumerate(accent_colors):
            accent_color_item = AnnotatedTableWidgetItem("   ")
            accent_color_item.setToolTip(
                f"H: {accent_color.hue} S: {accent_color.saturation} I: {accent_color.intensity}\n{accent_color}"
            )
            accent_color_item.annotated_data = (preset_index, step_index, _ACCENT_COLOR_PROPERTY_OFFSET + color_index)
            accent_color_item.setBackground(accent_color.to_qt_color())
            accent_color_item.setData(Qt.ItemDataRole.EditRole, accent_color)
            tw.setItem(row, _ACCENT_COLOR_COLUMN_OFFSET + color_index, accent_color_item)

    def _add_preset_buttons_to_table(
        self,
        preset_index: int,
        preset: ColorPreset,
        index_item: AnnotatedTableWidgetItem,
        first_row: int,
        last_row: int,
    ) -> None:
        """Add the widgets managing a preset to the table.

        The preset index and the asset management button are placed within the first row used by the preset. The
        buttons managing the steps and the preset itself are placed within the last row. Both widget groups are
        combined into a single cell widget if the preset uses one row only.

        Args:
            preset_index: The index of the preset within the model.
            preset: The preset the buttons manage.
            index_item: The table item holding the preset index within the first row.
            first_row: The first table row used by the preset.
            last_row: The last table row used by the preset.

        """
        tw = self._preset_table
        asset_mgmt_button = QPushButton()
        asset_mgmt_button.setIcon(_IMAGE_ICON)
        asset_mgmt_button.setToolTip("Select the visualization asset of this preset.")
        asset_mgmt_button.clicked.connect(lambda _, p=preset: self._change_preset_asset_clicked(p))
        asset_mgmt_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        management_layout = QHBoxLayout()
        add_step_button = QPushButton("↓")
        add_step_button.setToolTip("Add a step to this preset.")
        add_step_button.clicked.connect(lambda _, p=preset: self._add_step_to_preset(p))
        management_layout.addWidget(add_step_button)
        if len(preset.colors) > 1:
            remove_last_step_button = QPushButton("🗑")
            remove_last_step_button.setToolTip("Remove the last step from this preset.")
            remove_last_step_button.clicked.connect(lambda _, p=preset: self._remove_last_step_from_preset(p))
            management_layout.addSpacing(10)
            management_layout.addWidget(remove_last_step_button)
        remove_preset_button = QPushButton("❌")
        remove_preset_button.setToolTip("Remove this preset.")
        remove_preset_button.clicked.connect(lambda _, p=preset: self._remove_preset(p))
        management_layout.addSpacing(10)
        management_layout.addWidget(remove_preset_button)

        index_label = QLabel(str(preset_index))
        index_item.setText("")
        if first_row == last_row:
            # the preset uses a single row: combine the preset index, the management buttons and the asset button
            combined_layout = QHBoxLayout()
            combined_layout.addWidget(index_label)
            combined_layout.addStretch()
            combined_layout.addLayout(management_layout)
            combined_layout.addWidget(asset_mgmt_button)
            combined_widget = QWidget()
            combined_widget.setLayout(combined_layout)
            tw.setCellWidget(first_row, _PRESET_INDEX_COLUMN, combined_widget)
            return

        # the preset uses multiple rows: the first one shows the preset index and the asset management button
        header_layout = QHBoxLayout()
        header_layout.addWidget(index_label)
        header_layout.addWidget(asset_mgmt_button)
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        tw.setCellWidget(first_row, _PRESET_INDEX_COLUMN, header_widget)

        # the last row shows the buttons managing the steps and the preset
        last_row_layout = QHBoxLayout()
        last_row_layout.addStretch()
        last_row_layout.addLayout(management_layout)
        last_row_widget = QWidget()
        last_row_widget.setLayout(last_row_layout)
        tw.setCellWidget(last_row, _PRESET_INDEX_COLUMN, last_row_widget)

    def _preset_cell_edited(self, row: int, column: int) -> None:
        """Apply the value edited within a presets table cell to the model.

        Edits triggered while the table is rebuilt are ignored as they do not originate from the user. Cells that
        are not annotated or provide invalid position or edit data are reported and ignored: They indicate a bug
        within the table population.

        """
        if self._in_preset_table_rebuild:
            return
        item = self._preset_table.item(row, column)
        if not isinstance(item, AnnotatedTableWidgetItem):
            logger.error("Bug! Preset Cell %i:%i is not annotated!", row, column)
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
        if property_index == _FADE_IN_TIME_PROPERTY:
            edited_value = item.data(Qt.ItemDataRole.EditRole)
            if not isinstance(edited_value, int):
                logger.error("Bug! Cell %i:%i received an invalid fade in time: %r!", row, column, edited_value)
                return
            preset.colors[step_index] = (edited_value, tf, accent_colors)
            return
        if property_index == _TRANSFER_FUNCTION_PROPERTY:
            edited_value = item.data(Qt.ItemDataRole.EditRole)
            if not isinstance(edited_value, TransferFunction):
                logger.error("Bug! Cell %i:%i received invalid transfer function: %r!", row, column, edited_value)
                return
            preset.colors[step_index] = (fade_in_time, edited_value, accent_colors)
            return
        if property_index == _ADD_ACCENT_COLOR_PROPERTY:
            # the add accent color button is covered by a cell widget and its item is not editable
            return
        accent_color_index = property_index - _ACCENT_COLOR_PROPERTY_OFFSET
        if not (0 <= accent_color_index < len(accent_colors)):
            logger.error("Bug! cell %i:%i does not provide valid property: %i!", row, column, property_index)
            return
        color = item.data(Qt.ItemDataRole.EditRole)
        if not isinstance(color, ColorHSI):
            logger.error("Bug! Cell %i:%i received an invalid color: %r!", row, column, color)
            return
        accent_colors[accent_color_index] = color
        item.setBackground(color.to_qt_color())
        return

    def _load_default_colors_clicked_short(self) -> None:
        """Replace the presets by a short list of common colors and rebuild the tables."""
        self._model.populate_presets_with_initial_data(True)
        self._reload_presets_table()
        self._recall_tab.update_recall_table()

    def _load_default_colors_clicked_long(self) -> None:
        """Replace the presets by a long list of common colors and rebuild the tables."""
        self._model.populate_presets_with_initial_data(False)
        self._reload_presets_table()
        self._recall_tab.update_recall_table()

    def _add_preset(self) -> None:
        """Add a new empty preset to the model and rebuild the tables."""
        self._model.add_preset(ColorPreset())
        self._reload_presets_table()
        self._recall_tab.update_recall_table()

    def _add_accent_color(self, accent_color_list: list[ColorHSI]) -> None:
        """Append a white accent color to the accent colors of a preset step and rebuild the presets table.

        Args:
            accent_color_list: The accent color list of the preset step extended by another accent color.

        """
        accent_color_list.append(ColorHSI(0.0, 0.0, 1.0))
        self._reload_presets_table()

    def _add_step_to_preset(self, preset: ColorPreset) -> None:
        """Append a new step without accent colors to the preset and rebuild the presets table.

        Args:
            preset: The preset extended by another step.

        """
        preset.colors.append((0, TransferFunction.LINEAR, []))
        self._reload_presets_table()

    def _remove_last_step_from_preset(self, preset: ColorPreset) -> None:
        """Remove the last step from the preset and rebuild the presets table.

        Args:
            preset: The preset whose last step is removed. Presets without steps are ignored.

        """
        if len(preset.colors) == 0:
            return
        preset.colors.pop(-1)
        self._reload_presets_table()

    def _remove_preset(self, preset: ColorPreset) -> None:
        """Remove the provided preset from the model and rebuild the presets table.

        Args:
            preset: The preset to remove. Presets that are not part of the model are ignored.

        """
        if not self._model.remove_preset(preset):
            return
        self._reload_presets_table()
        self._recall_tab.update_recall_table()

    def _apply_live_preview_ui_state(self) -> None:
        """Synchronize the color groups tab and the live preview button with the model state."""
        preview_active = self._model.live_preview_mode
        self._color_groups_tab.setEnabled(not preview_active)
        self._widget.setTabEnabled(0, not preview_active)
        self._live_preview_button.setChecked(preview_active)

    def _live_preview_button_clicked(self, checked: bool) -> None:
        """Enable or disable the live preview mode depending on the new state of the toggle button."""
        if checked:
            self._enable_live_preview()
        else:
            self._disable_live_preview()

    def _enable_live_preview(self) -> None:
        """Enable the live preview mode and transmit the show to fish."""
        self._model.live_preview_mode = True
        self._widget.setCurrentIndex(1)
        self._apply_live_preview_ui_state()
        if not transmit_to_fish(self._model.scene.board_configuration, False):
            self._model.live_preview_mode = False
            self._widget.setCurrentIndex(0)
            self._apply_live_preview_ui_state()
            self._show_transmit_error_box(
                "Live Preview Unavailable",
                "Live preview could not be enabled because the show could not be transmitted to fish.",
            )

    def _disable_live_preview(self) -> None:
        """Disable the live preview mode and transmit the show without preview constants to fish."""
        if not self._model.live_preview_mode:
            return
        self._model.live_preview_mode = False
        self._widget.setCurrentIndex(0)
        self._apply_live_preview_ui_state()
        if not transmit_to_fish(self._model.scene.board_configuration, False):
            logger.error("Failed to transmit the show to fish while disabling the live preview mode.")
            self._show_transmit_error_box(
                "Live Preview Still Active",
                "The live preview could not be disabled because the show could not be transmitted to fish. "
                "The show on fish may still use the live preview constants. Transmit the show again to fix this.",
            )

    def _show_transmit_error_box(self, title: str, message: str) -> None:
        """Show a non-modal error box about a failed show transmission.

        Args:
            title: The window title of the message box.
            message: The message explaining the transmission failure.

        """
        error_box = QMessageBox(self._widget)
        error_box.setWindowTitle(title)
        error_box.setText(message)
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.show()

    def _preset_cell_clicked(self, row: int, column: int) -> None:
        """Apply the accent colors of the clicked preset step to the live preview while it is active."""
        if self._model.live_preview_mode:
            item = self._preset_table.item(row, column)
            if not isinstance(item, AnnotatedTableWidgetItem):
                logger.error("Preview Cell %i:%i is not annotated!", row, column)
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
        self._disable_live_preview()
        self._model.serialize()
        super().parent_closed(filter_node)

    def _change_preset_asset_clicked(self, preset: ColorPreset) -> None:
        """Open the asset selection dialog changing the visualization asset of the preset."""
        if self._asset_dialog is not None:
            self._asset_dialog.deleteLater()
        self._asset_dialog = AssetSelectionDialog(
            self._widget, preselected=preset.visualization_asset, allowed_types=[MediaType.IMAGE]
        )
        self._asset_dialog.setModal(True)
        self._asset_dialog.asset_selected.connect(lambda asset, p=preset: _set_asset(asset, p))
        self._asset_dialog.show()
