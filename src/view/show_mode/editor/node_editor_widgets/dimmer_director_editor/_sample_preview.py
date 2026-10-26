"""Reusable pyqtgraph preview widgets for the dimmer director editor."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pyqtgraph import PlotWidget, mkPen
from PySide6.QtGui import QPalette

from model.filters.dimmer_director import DimmerCurve, DimmerCurveType

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class SamplePreview(PlotWidget):
    """Plot a float sample list on a fixed [-1, 1] y axis."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Set up the plot item and the dark background matching the editor palette."""
        super().__init__(parent=parent)
        self.setYRange(-1.1, 1.1)
        self._data_line = self.plot()
        self._data_line.setPen(mkPen(width=2, color="#CC00AA"))
        self.setBackground(QPalette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window))
        self.setMouseEnabled(x=False, y=False)

    def set_samples(self, samples: list[float]) -> None:
        """Redraw the plot from the provided samples (empty list clears the plot)."""
        if not samples:
            self._data_line.setData([], [])
            self.setXRange(0, 1)
            return
        x = np.arange(len(samples), dtype=np.float32)
        y = np.asarray(samples, dtype=np.float32)
        self.setXRange(0, max(1, len(samples) - 1))
        self._data_line.setData(x, y)


class DimmerResponsePreview(PlotWidget):
    """Plot y = dimmer_curve(x) for x in [0, 1]."""

    _SAMPLES = 1000

    def __init__(self, parent: QWidget | None = None) -> None:
        """Set up the plot item and a square-ish [0, 1] view."""
        super().__init__(parent=parent)
        self.setYRange(-0.05, 1.05)
        self.setXRange(0.0, 1.0)
        self._data_line = self.plot()
        self._data_line.setPen(mkPen(width=2, color="#00AACC"))
        self.setBackground(QPalette().color(QPalette.ColorGroup.Normal, QPalette.ColorRole.Window))
        self.setMouseEnabled(x=False, y=False)

    def set_curve(self, curve: DimmerCurve | None) -> None:
        """Recompute the response plot for ``curve`` (clears when curve is None)."""
        if curve is None:
            self._data_line.setData([], [])
            return
        x = np.linspace(0.0, 1.0, self._SAMPLES, dtype=np.float64)
        y = _evaluate_dimmer_curve(curve, x)
        self._data_line.setData(x, y)


def _evaluate_dimmer_curve(curve: DimmerCurve, x: np.ndarray) -> np.ndarray:
    """Vectorised evaluation of the configured dimmer response curve."""
    match curve.type:
        case DimmerCurveType.LIN:
            # f(x) = a·x + b, clipped to [0, 1]. Default (a=1, b=0) is the identity.
            a = curve.params[0] if len(curve.params) >= 1 else 1.0
            b = curve.params[1] if len(curve.params) >= 2 else 0.0
            return np.clip(a * x + b, 0.0, 1.0)
        case DimmerCurveType.SIG:
            # steepened logistic centered at 0.5 — matches the fish description
            k = 10.0
            raw = 1.0 / (1.0 + np.exp(-k * (x - 0.5)))
            lo = 1.0 / (1.0 + np.exp(k * 0.5))
            hi = 1.0 / (1.0 + np.exp(-k * 0.5))
            return (raw - lo) / (hi - lo)
        case DimmerCurveType.BEZIER:
            params = curve.params if len(curve.params) >= 4 else [0.0, 0.0, 1.0, 1.0]
            p0, p1, p2, p3 = params[0], params[1], params[2], params[3]
            t = x
            return (
                (1 - t) ** 3 * p0
                + 3 * (1 - t) ** 2 * t * p1
                + 3 * (1 - t) * t ** 2 * p2
                + t ** 3 * p3
            )
    return x
