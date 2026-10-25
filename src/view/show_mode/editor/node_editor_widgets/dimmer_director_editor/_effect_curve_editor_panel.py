"""Effect curve editor panel: timeline + sample preview + CSV import controls."""

from __future__ import annotations

import csv
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from model.filter import DataType
from model.filter_data.cues.cue import Cue
from view.show_mode.editor.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.editor.node_editor_widgets.dimmer_director_editor._sample_preview import SamplePreview

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerDirectorFilter, EffectCurve

logger = getLogger(__name__)

_CSV_IMPORT_HELP = (
    "This effect curve was built from a CSV sample import. The timeline editor is disabled "
    "because the imported samples are the ground truth. Click 'Clear Imported Samples' to "
    "drop them and start editing keyframes."
)


class EffectCurveEditorPanel(QWidget):
    """Edit one effect curve: keyframes in a timeline plus a sample preview."""

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout. The panel is empty until ``set_curve_index`` is called."""
        super().__init__(parent)
        self._model = model
        self._curve_index: int | None = None
        layout = QVBoxLayout()
        header_row = QHBoxLayout()
        self._header_label = QLabel("No effect curve selected")
        header_row.addWidget(self._header_label)
        header_row.addStretch()
        self._import_button = QPushButton("Import samples from CSV")
        self._import_button.clicked.connect(self._import_csv)
        self._import_button.setEnabled(False)
        header_row.addWidget(self._import_button)
        self._clear_button = QPushButton("Clear Imported Samples")
        self._clear_button.clicked.connect(self._clear_samples)
        self._clear_button.setEnabled(False)
        header_row.addWidget(self._clear_button)
        self._resample_button = QPushButton("Rebuild samples from keyframes")
        self._resample_button.clicked.connect(self._resample)
        self._resample_button.setEnabled(False)
        header_row.addWidget(self._resample_button)
        layout.addLayout(header_row)

        self._help_label = QLabel(_CSV_IMPORT_HELP)
        self._help_label.setWordWrap(True)
        self._help_label.setVisible(False)
        layout.addWidget(self._help_label)

        splitter = QSplitter()
        self._timeline = TimelineContainer()
        splitter.addWidget(self._timeline)
        self._preview = SamplePreview()
        splitter.addWidget(self._preview)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)
        self.setLayout(layout)

        self._model.configuration_changed.mapped_signal.connect(self._refresh)

    def set_curve_index(self, index: int | None) -> None:
        """Switch the panel to display the effect curve at ``index`` (``None`` clears it)."""
        if self._curve_index is not None and self._curve_index != index:
            self._model.resample_effect_curve(self._curve_index)
        self._curve_index = index
        self._refresh()

    def _current_curve(self) -> EffectCurve | None:
        if self._curve_index is None:
            return None
        curves = self._model.effect_curves
        if not 0 <= self._curve_index < len(curves):
            return None
        return curves[self._curve_index]

    def _refresh(self) -> None:
        """Repopulate the timeline + preview + button states for the current curve."""
        curve = self._current_curve()
        if curve is None:
            self._header_label.setText("No effect curve selected")
            self._import_button.setEnabled(False)
            self._clear_button.setEnabled(False)
            self._resample_button.setEnabled(False)
            self._help_label.setVisible(False)
            self._timeline.setEnabled(False)
            self._timeline.cue = None
            self._preview.set_samples([])
            return
        self._header_label.setText(f"Editing effect curve '{curve.name}'")
        self._import_button.setEnabled(True)
        csv_mode = curve.is_csv_imported()
        self._clear_button.setEnabled(csv_mode)
        self._resample_button.setEnabled(not csv_mode)
        self._help_label.setVisible(csv_mode)
        self._timeline.setEnabled(not csv_mode)
        if curve.cue is None:
            curve.cue = Cue()
            curve.cue.add_channel("value", DataType.DT_DOUBLE)
        if self._timeline.cue is not curve.cue:
            self._timeline.cue = curve.cue
        self._preview.set_samples(curve.samples)

    def _resample(self) -> None:
        """Rebuild the sample cache from the current keyframes."""
        if self._curve_index is None:
            return
        self._model.resample_effect_curve(self._curve_index)

    def _clear_samples(self) -> None:
        """Drop CSV-imported samples so the user can resume keyframe editing."""
        if self._curve_index is None:
            return
        self._model.clear_effect_curve_samples(self._curve_index)

    def _import_csv(self) -> None:
        """Open a file dialog and replace the curve's samples with CSV values."""
        if self._curve_index is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import effect curve samples",
            "",
            "CSV files (*.csv);;All files (*)",
        )
        if not path:
            return
        try:
            values: list[float] = []
            with open(path, encoding="utf-8", newline="") as handle:
                for row in csv.reader(handle):
                    for raw_cell in row:
                        cell = raw_cell.strip()
                        if not cell:
                            continue
                        try:
                            values.append(float(cell))
                        except ValueError:
                            logger.warning("Skipping non-numeric cell %r in %s", cell, path)
        except OSError as exc:
            logger.error("Failed to read %s: %s", path, exc)
            return
        if not values:
            return
        self._model.import_effect_curve_samples(self._curve_index, values)

    def apply_pending_resample(self) -> None:
        """Flush any pending keyframe edits by rebuilding the sample cache."""
        if self._curve_index is None:
            return
        self._model.resample_effect_curve(self._curve_index)
