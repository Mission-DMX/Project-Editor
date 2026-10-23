"""Settings widget for the ``filter_series_strobe_generator_*`` filter family."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from view.show_mode.editor.node_editor_widgets.node_editor_widget import NodeEditorFilterConfigWidget
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox

if TYPE_CHECKING:
    from model import Filter


_DEFAULT_SLOWEST_PERIOD_MS = 500.0
_MIN_FREQ_HZ = 0.01
_MAX_FREQ_HZ = 20.0
_HELP_TEXT = (
    "Frequency produced when the frequency input equals 1 — the slowest strobe rate "
    "this filter can emit. Higher input values interpolate linearly up to 20 Hz. A "
    "frequency input of 0 disables strobing and passes the brightness through unchanged."
)


class StrobeGeneratorConfigWidget(NodeEditorFilterConfigWidget):
    """Expose ``slowest_period_ms`` as a jogwheel-driven lowest-frequency spinbox."""

    def __init__(self, _filter: Filter) -> None:
        """Build the widget. The filter reference is kept for parity with other widgets."""
        super().__init__()
        self._filter = _filter
        self._widget = QWidget()

        self._freq_spinbox = JogwheelDoubleSpinBox(self._widget)
        self._freq_spinbox.setMinimum(_MIN_FREQ_HZ)
        self._freq_spinbox.setMaximum(_MAX_FREQ_HZ)
        self._freq_spinbox.setDecimals(2)
        self._freq_spinbox.setSingleStep(0.1)
        self._freq_spinbox.setSuffix(" Hz")
        self._freq_spinbox.setValue(1000.0 / _DEFAULT_SLOWEST_PERIOD_MS)

        help_label = QLabel(_HELP_TEXT, self._widget)
        help_label.setWordWrap(True)
        help_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        form = QFormLayout()
        form.addRow("Lowest frequency", self._freq_spinbox)

        outer = QVBoxLayout(self._widget)
        outer.addLayout(form)
        outer.addWidget(help_label)

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        try:
            period_ms = float(conf.get("slowest_period_ms", str(_DEFAULT_SLOWEST_PERIOD_MS)))
        except ValueError:
            period_ms = _DEFAULT_SLOWEST_PERIOD_MS
        if period_ms <= 0.0:
            period_ms = _DEFAULT_SLOWEST_PERIOD_MS
        freq_hz = max(min(1000.0 / period_ms, _MAX_FREQ_HZ), _MIN_FREQ_HZ)
        self._freq_spinbox.setValue(freq_hz)

    @override
    def _get_configuration(self) -> dict[str, str]:
        freq_hz = max(self._freq_spinbox.value(), _MIN_FREQ_HZ)
        period_ms = 1000.0 / freq_hz
        return {"slowest_period_ms": f"{period_ms:.3f}"}

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        pass

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}

    @override
    def parent_opened(self) -> None:
        pass
