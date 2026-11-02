"""Effect curve editor panel: timeline + sample preview + CSV/sine import controls."""

from __future__ import annotations

import csv
import os
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from model.filter import DataType
from model.filter_data.cues.cue import Cue, KeyFrame, StateDouble
from view.show_mode.editor.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.editor.node_editor_widgets.dimmer_director_editor._sample_preview import SamplePreview
from view.show_mode.editor.node_editor_widgets.dimmer_director_editor._sine_generator_dialog import (
    SineGeneratorDialog,
)
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

if TYPE_CHECKING:
    from model.filters.dimmer_director import DimmerDirectorFilter, EffectCurve

logger = getLogger(__name__)

_CSV_IMPORT_HELP = (
    "This effect curve was built from a CSV sample import. The timeline editor is disabled "
    "because the imported samples are the ground truth. Click 'Clear Imported Samples' to "
    "drop them and start editing keyframes."
)


class _ResampleWorker(QThread):
    """QThread that resamples an effect curve's keyframes without blocking the UI."""

    finished_for_index = Signal(int)

    def __init__(self, model: DimmerDirectorFilter, curve_index: int) -> None:
        """Capture the curve index whose samples the thread will rebuild on ``run``."""
        super().__init__()
        self._model = model
        self._curve_index = curve_index

    def run(self) -> None:
        """Rebuild samples from keyframes on the worker thread."""
        self._model.resample_effect_curve(self._curve_index)
        self.finished_for_index.emit(self._curve_index)


class EffectCurveEditorPanel(QWidget):
    """Edit one effect curve: keyframes in a timeline plus a sample preview."""

    def __init__(self, model: DimmerDirectorFilter, parent: QWidget | None = None) -> None:
        """Build the layout. The panel is empty until ``set_curve_index`` is called."""
        super().__init__(parent)
        self._model = model
        self._curve_index: int | None = None
        self._active_worker: _ResampleWorker | None = None
        self._sine_dialog: SineGeneratorDialog | None = None
        layout = QVBoxLayout()
        header_row = QHBoxLayout()
        self._header_label = QLabel("No effect curve selected")
        header_row.addWidget(self._header_label)
        header_row.addStretch()
        self._import_button = QPushButton("Import samples from CSV")
        self._import_button.clicked.connect(self._import_csv)
        self._import_button.setEnabled(False)
        header_row.addWidget(self._import_button)
        self._sine_button = QPushButton("Generate sine curve…")
        self._sine_button.clicked.connect(self._open_sine_dialog)
        self._sine_button.setEnabled(False)
        header_row.addWidget(self._sine_button)
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

        record_row = QHBoxLayout()
        record_row.addWidget(QLabel("Value:"))
        self._record_value_sb = JogwheelDoubleSpinBox()
        self._record_value_sb.setRange(-1.0, 1.0)
        self._record_value_sb.setSingleStep(0.05)
        self._record_value_sb.setDecimals(4)
        self._record_value_sb.setValue(0.0)
        record_row.addWidget(self._record_value_sb)
        record_row.addWidget(QLabel("Transition:"))
        self._record_transition_cb = QComboBox()
        for key, label in (("edg", "edge"), ("lin", "linear"), ("sig", "sigmoidal"),
                           ("e_i", "ease in"), ("e_o", "ease out")):
            self._record_transition_cb.addItem(label, key)
        self._record_transition_cb.setCurrentIndex(1)
        record_row.addWidget(self._record_transition_cb)
        self._record_button = QPushButton("Record keyframe at cursor")
        self._record_button.clicked.connect(self._record_keyframe)
        self._record_button.setEnabled(False)
        record_row.addWidget(self._record_button)
        record_row.addStretch()
        layout.addLayout(record_row)

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
        """Switch the panel to display the effect curve at ``index`` (``None`` clears it).

        If a different curve was previously selected and had keyframes, kick off a
        background resample for that curve before switching so the sample cache stays in
        sync with the user's edits.
        """
        previous_index = self._curve_index
        if previous_index is not None and previous_index != index:
            self._start_background_resample(previous_index)
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
            self._sine_button.setEnabled(False)
            self._clear_button.setEnabled(False)
            self._resample_button.setEnabled(False)
            self._record_button.setEnabled(False)
            self._help_label.setVisible(False)
            self._timeline.setEnabled(False)
            self._timeline.cue = None
            self._preview.set_samples([])
            return
        self._header_label.setText(f"Editing effect curve '{curve.name}'")
        self._import_button.setEnabled(True)
        self._sine_button.setEnabled(True)
        csv_mode = curve.is_csv_imported()
        self._clear_button.setEnabled(csv_mode)
        self._resample_button.setEnabled(not csv_mode)
        self._record_button.setEnabled(not csv_mode)
        self._help_label.setVisible(csv_mode)
        self._timeline.setEnabled(not csv_mode)
        if curve.cue is None:
            curve.cue = Cue()
            curve.cue.add_channel("value", DataType.DT_DOUBLE)
        if self._timeline.cue is not curve.cue:
            self._timeline.cue = curve.cue
        self._preview.set_samples(curve.samples)

    def _record_keyframe(self) -> None:
        """Insert a keyframe at the current cursor position using the user-entered value."""
        curve = self._current_curve()
        if curve is None or curve.is_csv_imported():
            return
        if curve.cue is None:
            curve.cue = Cue()
            curve.cue.add_channel("value", DataType.DT_DOUBLE)
        transition = self._record_transition_cb.currentData() or "lin"
        value = float(self._record_value_sb.value())
        timestamp = float(self._timeline.cursor_position)
        frame = KeyFrame(curve.cue)
        frame.timestamp = max(0.0, timestamp)
        state = StateDouble(transition)
        state._value = value
        frame.append_state(state)
        curve.cue.insert_frame(frame)
        self._timeline.update_cue_display()
        self._model.configuration_changed.mapped_signal.emit()
        if self._curve_index is not None:
            self._start_background_resample(self._curve_index)

    def _resample(self) -> None:
        """Rebuild the sample cache from the current keyframes (synchronous explicit action)."""
        if self._curve_index is None:
            return
        self._model.resample_effect_curve(self._curve_index)

    def _clear_samples(self) -> None:
        """Drop CSV-imported samples so the user can resume keyframe editing."""
        if self._curve_index is None:
            return
        self._model.clear_effect_curve_samples(self._curve_index)

    def _import_csv(self) -> None:
        """Open a file dialog (defaulting to the user's home) and import CSV samples."""
        if self._curve_index is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import effect curve samples",
            os.path.expanduser("~"),
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

    def _open_sine_dialog(self) -> None:
        """Open the modal sine-wave generator dialog and apply the result on accept."""
        if self._curve_index is None:
            return
        if self._sine_dialog is not None:
            self._sine_dialog.deleteLater()
        dialog = SineGeneratorDialog(self)
        self._sine_dialog = dialog
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        samples = dialog.generate_samples()
        if not samples:
            return
        self._model.import_effect_curve_samples(self._curve_index, samples)

    def _start_background_resample(self, curve_index: int) -> None:
        """Kick off a worker thread to resample ``curve_index`` from its keyframes.

        If a worker is already running we wait for it to finish first — the pipeline is
        intentionally serialised to keep ``filter_configurations`` and ``samples``
        consistent at any observation point.
        """
        self._join_active_worker()
        curves = self._model.effect_curves
        if not 0 <= curve_index < len(curves):
            return
        curve = curves[curve_index]
        if curve.is_csv_imported() or curve.cue is None or len(curve.cue._frames) == 0:
            return
        worker = _ResampleWorker(self._model, curve_index)
        worker.finished_for_index.connect(self._worker_finished)
        self._active_worker = worker
        worker.start()

    def _worker_finished(self, _curve_index: int) -> None:
        """Clear the ``_active_worker`` reference once the thread completes."""
        if self._active_worker is not None and self._active_worker.isFinished():
            self._active_worker.deleteLater()
            self._active_worker = None

    def _join_active_worker(self) -> None:
        """Wait for the current resample worker (if any) to finish."""
        worker = self._active_worker
        if worker is None:
            return
        if worker.isRunning():
            worker.wait()
        worker.deleteLater()
        self._active_worker = None

    def apply_pending_resample(self) -> None:
        """Flush any pending resample work.

        Called before the config dialog's ``_get_configuration`` / ``_get_parameters`` /
        ``parent_closed`` return paths. Joins the worker thread (if one is running) and
        then resamples the current curve synchronously so the just-edited keyframes also
        reach the ``filter_configurations`` dict.
        """
        self._join_active_worker()
        if self._curve_index is None:
            return
        self._model.resample_effect_curve(self._curve_index)
