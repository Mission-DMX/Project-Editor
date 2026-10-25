"""Curves tab: effect-curve table + dimmer-curve table + stacked editor panel."""

from __future__ import annotations

import os
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from model.filters.dimmer_director import EffectCurveMode
from model.media_assets.image import AbstractImageAsset
from model.media_assets.media_type import MediaType
from utility import resource_path
from view.dialogs.asset_selection_dialog import AssetSelectionDialog
from view.show_mode.editor.node_editor_widgets.dimmer_director_editor._dimmer_curve_editor_panel import (
    DimmerCurveEditorPanel,
)
from view.show_mode.editor.node_editor_widgets.dimmer_director_editor._effect_curve_editor_panel import (
    EffectCurveEditorPanel,
)

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerCurve, DimmerDirectorFilter, EffectCurve
    from model.media_assets.asset import MediaAsset

logger = getLogger(__name__)
_IMAGE_ICON = QIcon(resource_path(os.path.join("resources", "icons", "media_image.svg")))

_EFFECT_COLUMNS = ["Name", "Icon", "Mode", "Threshold", "Window"]
_DIMMER_COLUMNS = ["Name", "Icon", "Type"]


class CurvesTab(QWidget):
    """Side-by-side tables for the two curve kinds plus the switching editor panel."""

    curves_changed = Signal()

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout and connect the model's configuration_changed signal."""
        super().__init__(parent)
        self._model = model
        self._in_rebuild = False
        self._asset_dialog: AssetSelectionDialog | None = None
        self._asset_target: tuple[str, int] | None = None

        root_layout = QVBoxLayout()

        tables_row = QHBoxLayout()

        effect_container = QWidget()
        effect_layout = QVBoxLayout()
        effect_layout.setContentsMargins(0, 0, 0, 0)
        effect_buttons = QHBoxLayout()
        add_effect_btn = QPushButton("Add Effect Curve")
        add_effect_btn.clicked.connect(self._add_effect_curve)
        effect_buttons.addWidget(add_effect_btn)
        remove_effect_btn = QPushButton("Remove Selected")
        remove_effect_btn.clicked.connect(self._remove_effect_curve)
        effect_buttons.addWidget(remove_effect_btn)
        effect_buttons.addStretch()
        effect_layout.addLayout(effect_buttons)
        self._effect_table = QTableWidget()
        self._effect_table.setColumnCount(len(_EFFECT_COLUMNS))
        self._effect_table.setHorizontalHeaderLabels(_EFFECT_COLUMNS)
        self._effect_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(_EFFECT_COLUMNS)):
            self._effect_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self._effect_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._effect_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._effect_table.itemSelectionChanged.connect(self._effect_selection_changed)
        self._effect_table.itemChanged.connect(self._effect_item_changed)
        effect_layout.addWidget(self._effect_table)
        effect_container.setLayout(effect_layout)
        tables_row.addWidget(effect_container)

        dimmer_container = QWidget()
        dimmer_layout = QVBoxLayout()
        dimmer_layout.setContentsMargins(0, 0, 0, 0)
        dimmer_buttons = QHBoxLayout()
        add_dimmer_btn = QPushButton("Add Dimmer Curve")
        add_dimmer_btn.clicked.connect(self._add_dimmer_curve)
        dimmer_buttons.addWidget(add_dimmer_btn)
        remove_dimmer_btn = QPushButton("Remove Selected")
        remove_dimmer_btn.clicked.connect(self._remove_dimmer_curve)
        dimmer_buttons.addWidget(remove_dimmer_btn)
        dimmer_buttons.addStretch()
        dimmer_layout.addLayout(dimmer_buttons)
        self._dimmer_table = QTableWidget()
        self._dimmer_table.setColumnCount(len(_DIMMER_COLUMNS))
        self._dimmer_table.setHorizontalHeaderLabels(_DIMMER_COLUMNS)
        self._dimmer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(_DIMMER_COLUMNS)):
            self._dimmer_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self._dimmer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._dimmer_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._dimmer_table.itemSelectionChanged.connect(self._dimmer_selection_changed)
        self._dimmer_table.itemChanged.connect(self._dimmer_item_changed)
        dimmer_layout.addWidget(self._dimmer_table)
        dimmer_container.setLayout(dimmer_layout)
        tables_row.addWidget(dimmer_container)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        tables_widget = QWidget()
        tables_widget.setLayout(tables_row)
        splitter.addWidget(tables_widget)

        self._editor_stack = QStackedWidget()
        self._empty_page = QWidget()
        self._editor_stack.addWidget(self._empty_page)
        self._effect_panel = EffectCurveEditorPanel(model)
        self._editor_stack.addWidget(self._effect_panel)
        self._dimmer_panel = DimmerCurveEditorPanel(model)
        self._editor_stack.addWidget(self._dimmer_panel)
        splitter.addWidget(self._editor_stack)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root_layout.addWidget(splitter)
        self.setLayout(root_layout)

        self._refresh_tables()
        self._model.configuration_changed.mapped_signal.connect(self._refresh_tables)

    # ---------------------------------------------------------------- tables

    def _refresh_tables(self) -> None:
        """Rebuild both tables from the current model state, preserving the selection."""
        self._in_rebuild = True
        try:
            effect_row = self._effect_table.currentRow()
            dimmer_row = self._dimmer_table.currentRow()
            self._fill_effect_table()
            self._fill_dimmer_table()
            if 0 <= effect_row < self._effect_table.rowCount():
                self._effect_table.selectRow(effect_row)
            if 0 <= dimmer_row < self._dimmer_table.rowCount():
                self._dimmer_table.selectRow(dimmer_row)
        finally:
            self._in_rebuild = False

    def _fill_effect_table(self) -> None:
        """Populate the effect-curves table."""
        curves = self._model.effect_curves
        self._effect_table.setRowCount(len(curves))
        for row, curve in enumerate(curves):
            self._effect_table.setItem(row, 0, QTableWidgetItem(curve.name))
            self._set_icon_cell(self._effect_table, row, 1, curve, kind="effect")
            self._set_mode_cell(row, curve)
            threshold_item = QTableWidgetItem(f"{curve.threshold:g}")
            threshold_item.setData(Qt.ItemDataRole.UserRole, curve.threshold)
            if curve.mode == EffectCurveMode.REPEAT:
                # Threshold is only consulted by fish in TRIGGER mode (see effects.md).
                threshold_item.setFlags(threshold_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                threshold_item.setToolTip("Threshold is only used by TRIGGER-mode curves.")
            self._effect_table.setItem(row, 3, threshold_item)
            window_item = QTableWidgetItem(str(curve.window))
            window_item.setData(Qt.ItemDataRole.UserRole, curve.window)
            self._effect_table.setItem(row, 4, window_item)

    def _fill_dimmer_table(self) -> None:
        """Populate the dimmer-curves table."""
        curves = self._model.dimmer_curves
        self._dimmer_table.setRowCount(len(curves))
        for row, curve in enumerate(curves):
            self._dimmer_table.setItem(row, 0, QTableWidgetItem(curve.name))
            self._set_icon_cell(self._dimmer_table, row, 1, curve, kind="dimmer")
            self._set_type_cell(row, curve)

    def _set_icon_cell(
        self,
        table: QTableWidget,
        row: int,
        column: int,
        curve: EffectCurve | DimmerCurve,
        kind: str,
    ) -> None:
        """Place the per-row 'Set Icon' button or configured icon in the table cell."""
        asset = curve.icon_asset
        button = QPushButton()
        if asset is not None:
            qt_icon = _asset_to_icon(asset)
            if qt_icon is not None:
                button.setIcon(qt_icon)
        else:
            button.setIcon(_IMAGE_ICON)
        button.setToolTip("Select the icon shown on the runtime button.")
        button.clicked.connect(lambda _checked=False, k=kind, r=row: self._open_asset_dialog(k, r))
        table.setCellWidget(row, column, button)

    def _set_mode_cell(self, row: int, curve: EffectCurve) -> None:
        """Place the mode / threshold cells for an effect curve."""
        combo = QComboBox()
        for mode in EffectCurveMode:
            combo.addItem(mode.value, mode)
        idx = combo.findData(curve.mode)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda _idx=0, r=row: self._effect_mode_changed(r))
        self._effect_table.setCellWidget(row, 2, combo)

    def _set_type_cell(self, row: int, curve: DimmerCurve) -> None:
        """Place the type combo for a dimmer curve."""
        from model.filters.dimmer_director import DimmerCurveType

        combo = QComboBox()
        for ct in DimmerCurveType:
            combo.addItem(ct.value, ct)
        idx = combo.findData(curve.type)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda _idx=0, r=row: self._dimmer_type_changed(r))
        self._dimmer_table.setCellWidget(row, 2, combo)

    # ------------------------------------------------------------- selection

    def _effect_selection_changed(self) -> None:
        """Switch the editor stack to the effect-curve panel for the selected row."""
        if self._in_rebuild:
            return
        row = self._effect_table.currentRow()
        self._dimmer_table.clearSelection()
        if row < 0:
            self._editor_stack.setCurrentWidget(self._empty_page)
            return
        self._effect_panel.set_curve_index(row)
        self._editor_stack.setCurrentWidget(self._effect_panel)

    def _dimmer_selection_changed(self) -> None:
        """Switch the editor stack to the dimmer-curve panel for the selected row."""
        if self._in_rebuild:
            return
        row = self._dimmer_table.currentRow()
        self._effect_table.clearSelection()
        if row < 0:
            self._editor_stack.setCurrentWidget(self._empty_page)
            return
        self._dimmer_panel.set_curve_index(row)
        self._editor_stack.setCurrentWidget(self._dimmer_panel)

    # ----------------------------------------------------------------- edits

    def _effect_item_changed(self, item: QTableWidgetItem) -> None:
        """Apply direct cell edits (name, threshold, window) to the model."""
        if self._in_rebuild:
            return
        row = item.row()
        curves = self._model.effect_curves
        if not 0 <= row < len(curves):
            return
        curve = curves[row]
        match item.column():
            case 0:
                curve.name = item.text()
            case 3:
                try:
                    curve.threshold = max(0.0, min(1.0, float(item.text())))
                except ValueError:
                    self._refresh_tables()
                    return
            case 4:
                try:
                    curve.window = max(1, int(item.text()))
                except ValueError:
                    self._refresh_tables()
                    return
            case _:
                return
        self._model.configuration_changed.mapped_signal.emit()
        self.curves_changed.emit()

    def _dimmer_item_changed(self, item: QTableWidgetItem) -> None:
        """Apply direct cell edits (name) to the model."""
        if self._in_rebuild:
            return
        row = item.row()
        curves = self._model.dimmer_curves
        if not 0 <= row < len(curves):
            return
        curve = curves[row]
        if item.column() == 0:
            curve.name = item.text()
            self._model.configuration_changed.mapped_signal.emit()
            self.curves_changed.emit()

    def _effect_mode_changed(self, row: int) -> None:
        """Push a mode combo change back to the model."""
        if self._in_rebuild:
            return
        combo = self._effect_table.cellWidget(row, 2)
        if not isinstance(combo, QComboBox):
            return
        mode = combo.currentData()
        if not isinstance(mode, EffectCurveMode):
            return
        curves = self._model.effect_curves
        if not 0 <= row < len(curves):
            return
        if curves[row].mode == mode:
            return
        curves[row].mode = mode
        self._model.configuration_changed.mapped_signal.emit()
        self.curves_changed.emit()

    def _dimmer_type_changed(self, row: int) -> None:
        """Push a dimmer-curve type combo change back to the model."""
        if self._in_rebuild:
            return
        combo = self._dimmer_table.cellWidget(row, 2)
        if not isinstance(combo, QComboBox):
            return
        from model.filters.dimmer_director import DimmerCurveType

        new_type = combo.currentData()
        if not isinstance(new_type, DimmerCurveType):
            return
        curves = self._model.dimmer_curves
        if not 0 <= row < len(curves):
            return
        if curves[row].type == new_type:
            return
        curves[row].type = new_type
        if new_type == DimmerCurveType.BEZIER and len(curves[row].params) < 4:
            curves[row].params = [0.0, 0.0, 1.0, 1.0]
        self._model.configuration_changed.mapped_signal.emit()
        self.curves_changed.emit()

    # ----------------------------------------------------------- add/remove

    def _add_effect_curve(self) -> None:
        self._model.add_effect_curve()
        self.curves_changed.emit()

    def _remove_effect_curve(self) -> None:
        row = self._effect_table.currentRow()
        if row < 0:
            return
        if self._model.remove_effect_curve(row):
            self.curves_changed.emit()

    def _add_dimmer_curve(self) -> None:
        self._model.add_dimmer_curve()
        self.curves_changed.emit()

    def _remove_dimmer_curve(self) -> None:
        row = self._dimmer_table.currentRow()
        if row < 0:
            return
        if self._model.remove_dimmer_curve(row):
            self.curves_changed.emit()

    # --------------------------------------------------------------- icons

    def _open_asset_dialog(self, kind: str, row: int) -> None:
        """Launch the shared asset-selection dialog scoped to IMAGE assets."""
        if self._asset_dialog is not None:
            self._asset_dialog.deleteLater()
        self._asset_target = (kind, row)
        preselected = None
        if kind == "effect":
            curves = self._model.effect_curves
            if 0 <= row < len(curves):
                preselected = curves[row].icon_asset
        else:
            curves = self._model.dimmer_curves
            if 0 <= row < len(curves):
                preselected = curves[row].icon_asset
        self._asset_dialog = AssetSelectionDialog(
            self, preselected=preselected, allowed_types=[MediaType.IMAGE],
        )
        self._asset_dialog.setModal(True)
        self._asset_dialog.asset_selected.connect(self._asset_selected)
        self._asset_dialog.show()

    def _asset_selected(self, assets: list[MediaAsset]) -> None:
        """Apply the chosen image asset to the targeted curve."""
        if self._asset_target is None:
            return
        kind, row = self._asset_target
        self._asset_target = None
        asset: AbstractImageAsset | None = None
        if assets:
            first = assets[0]
            if isinstance(first, AbstractImageAsset):
                asset = first
        if kind == "effect":
            curves = self._model.effect_curves
            if 0 <= row < len(curves):
                curves[row].icon_asset = asset
        else:
            curves = self._model.dimmer_curves
            if 0 <= row < len(curves):
                curves[row].icon_asset = asset
        self._model.configuration_changed.mapped_signal.emit()
        self.curves_changed.emit()

    def apply_pending_resample(self) -> None:
        """Flush any pending effect-curve keyframe edits (called before save/close)."""
        self._effect_panel.apply_pending_resample()


def _asset_to_icon(asset: AbstractImageAsset) -> QIcon | None:
    """Return a QIcon for the asset, or None if the asset cannot be rendered."""
    try:
        image = asset.get_image_for_ui()
    except Exception:
        return None
    if image is None:
        return None
    pixmap = QPixmap.fromImage(image)
    if pixmap.isNull():
        return None
    return QIcon(pixmap)
