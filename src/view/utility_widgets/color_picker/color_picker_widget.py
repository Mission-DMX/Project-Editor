"""Composite color picker widget.

Combines the CIE 1931 xy chromaticity diagram (`ChromaticityDiagramGLWidget`)
with synchronized numeric inputs for HSI, RGB, CMY and an HTML hex field.

Public API (preserved from the previous stub):
    * ``color_changed = Signal(ColorHSI)`` — fires once per committed change,
      including during live mouse drag on the diagram.
    * ``color`` property — getter returns the current ``ColorHSI``, setter
      updates all inputs and emits ``color_changed`` on actual changes.

Note on the "intensity" axis: ``ColorHSI`` uses the HSV ``V`` channel (the
max-of-RGB brightness), not the CIE ``Y`` relative luminance.  For picker
purposes this value is routed into the shader's ``uY`` uniform; the result is
the standard "diagram dims with the slider" behaviour that Krita / GIMP /
DearWidgets ship.
"""

from __future__ import annotations

from logging import getLogger

from PySide6.QtCore import QRegularExpression, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QPalette, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from model.color_hsi import ColorHSI
from view.utility_widgets.color_picker import cie_constants as cie
from view.utility_widgets.color_picker.chromaticity_gl_widget import ChromaticityDiagramGLWidget
from view.utility_widgets.jogwheel_spinbox import JogwheelDoubleSpinBox, JogwheelSpinBox

logger = getLogger(__name__)


_INTENSITY_SLIDER_RESOLUTION = 1000


class ColorPickerWidget(QWidget):
    """Composite color picker: chromaticity diagram + HSI/RGB/CMY inputs + intensity slider."""

    color_changed: Signal = Signal(ColorHSI)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the composite layout and seed the inputs with the initial color."""
        super().__init__(parent)

        self.setMinimumSize(800, 600)

        self._color: ColorHSI = ColorHSI(0.0, 0.0, 1.0)
        self._updating: bool = False

        # --- OpenGL chromaticity diagram ---
        self._chromaticity = ChromaticityDiagramGLWidget(self)
        self._chromaticity.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._chromaticity.xy_picked.connect(self._on_xy_picked)

        # --- Preview swatch ---
        self._preview = QFrame(self)
        self._preview.setMinimumHeight(40)
        self._preview.setAutoFillBackground(True)
        self._preview.setFrameShape(QFrame.Shape.Panel)
        self._preview.setFrameShadow(QFrame.Shadow.Sunken)

        # --- Intensity slider ---
        self._intensity_slider = QSlider(Qt.Orientation.Vertical, self)
        self._intensity_slider.setRange(0, _INTENSITY_SLIDER_RESOLUTION)
        self._intensity_slider.setValue(_INTENSITY_SLIDER_RESOLUTION)
        self._intensity_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self._intensity_slider.setTickInterval(_INTENSITY_SLIDER_RESOLUTION // 10)
        self._intensity_slider.valueChanged.connect(self._on_intensity_slider_changed)

        # --- HSI inputs ---
        self._hue_spin = JogwheelDoubleSpinBox(self)
        self._hue_spin.setRange(0.0, 359.9)
        self._hue_spin.setDecimals(1)
        self._hue_spin.setSingleStep(1.0)
        self._hue_spin.setSuffix("°")
        self._sat_spin = JogwheelDoubleSpinBox(self)
        self._sat_spin.setRange(0.0, 100.0)
        self._sat_spin.setDecimals(1)
        self._sat_spin.setSingleStep(1.0)
        self._sat_spin.setSuffix(" %")
        self._int_spin = JogwheelDoubleSpinBox(self)
        self._int_spin.setRange(0.0, 100.0)
        self._int_spin.setDecimals(1)
        self._int_spin.setSingleStep(1.0)
        self._int_spin.setSuffix(" %")

        for spin in (self._hue_spin, self._sat_spin, self._int_spin):
            spin.valueChanged.connect(self._on_hsi_changed)

        # --- RGB inputs ---
        self._r_spin = JogwheelSpinBox(self)
        self._g_spin = JogwheelSpinBox(self)
        self._b_spin = JogwheelSpinBox(self)
        for spin in (self._r_spin, self._g_spin, self._b_spin):
            spin.setRange(0, 255)
            spin.setSingleStep(1)
            spin.valueChanged.connect(self._on_rgb_changed)

        # --- CMY inputs ---
        self._c_spin = JogwheelDoubleSpinBox(self)
        self._m_spin = JogwheelDoubleSpinBox(self)
        self._y_spin = JogwheelDoubleSpinBox(self)
        for spin in (self._c_spin, self._m_spin, self._y_spin):
            spin.setRange(0.0, 100.0)
            spin.setDecimals(1)
            spin.setSingleStep(1.0)
            spin.setSuffix(" %")
            spin.valueChanged.connect(self._on_cmy_changed)

        # --- Hex input ---
        self._hex_edit = QLineEdit(self)
        self._hex_edit.setPlaceholderText("#RRGGBB")
        self._hex_edit.setMaxLength(7)
        self._hex_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^#?[0-9A-Fa-f]{6}$"), self),
        )
        self._hex_edit.editingFinished.connect(self._on_hex_edited)

        self._build_layout()

        # Seed the UI with the initial color.
        self._refresh_all_from_color()

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    @property
    def color(self) -> ColorHSI:
        """Return a copy of the currently-selected color."""
        return self._color.copy()

    @color.setter
    def color(self, new_color: ColorHSI) -> None:
        """Set the current color.

        Emits ``color_changed`` only when the value actually differs.
        """
        self._apply_color(new_color, origin="external")

    # -----------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------

    def _build_layout(self) -> None:
        root = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(self._chromaticity, 1)
        left.addWidget(self._preview)
        root.addLayout(left, 3)

        slider_box = QVBoxLayout()
        slider_label = QLabel("Intensity", self)
        slider_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        slider_box.addWidget(slider_label)
        slider_box.addWidget(self._intensity_slider, 1, Qt.AlignmentFlag.AlignHCenter)
        root.addLayout(slider_box)

        right = QVBoxLayout()

        hsi_group = QGroupBox("HSI", self)
        hsi_form = QFormLayout(hsi_group)
        hsi_form.addRow("Hue", self._hue_spin)
        hsi_form.addRow("Saturation", self._sat_spin)
        hsi_form.addRow("Intensity", self._int_spin)
        right.addWidget(hsi_group)

        rgb_group = QGroupBox("RGB", self)
        rgb_form = QFormLayout(rgb_group)
        rgb_form.addRow("Red", self._r_spin)
        rgb_form.addRow("Green", self._g_spin)
        rgb_form.addRow("Blue", self._b_spin)
        right.addWidget(rgb_group)

        cmy_group = QGroupBox("CMY", self)
        cmy_form = QFormLayout(cmy_group)
        cmy_form.addRow("Cyan", self._c_spin)
        cmy_form.addRow("Magenta", self._m_spin)
        cmy_form.addRow("Yellow", self._y_spin)
        right.addWidget(cmy_group)

        hex_group = QGroupBox("Hex", self)
        hex_form = QFormLayout(hex_group)
        hex_form.addRow("HTML", self._hex_edit)
        right.addWidget(hex_group)

        right.addStretch(1)
        root.addLayout(right, 2)

    # -----------------------------------------------------------------
    # Signal flow
    # -----------------------------------------------------------------

    def _apply_color(self, new_color: ColorHSI, origin: str) -> None:
        if self._updating:
            return
        if new_color == self._color:
            return
        self._updating = True
        try:
            self._color = new_color.copy()
            self._refresh_all_from_color(exclude=origin)
        finally:
            self._updating = False
        self.color_changed.emit(self._color.copy())

    def _refresh_all_from_color(self, exclude: str | None = None) -> None:
        self._refresh_hsi(skip=(exclude == "hsi"))
        self._refresh_rgb(skip=(exclude == "rgb"))
        self._refresh_cmy(skip=(exclude == "cmy"))
        self._refresh_hex(skip=(exclude == "hex"))
        self._refresh_intensity_slider(skip=(exclude == "intensity_slider"))
        self._refresh_diagram(skip=(exclude == "chromaticity"))
        self._refresh_preview()

    def _refresh_hsi(self, *, skip: bool = False) -> None:
        if skip:
            return
        with QSignalBlocker(self._hue_spin), QSignalBlocker(self._sat_spin), QSignalBlocker(self._int_spin):
            self._hue_spin.setValue(self._color.hue)
            self._sat_spin.setValue(self._color.saturation * 100.0)
            self._int_spin.setValue(self._color.intensity * 100.0)

    def _refresh_rgb(self, *, skip: bool = False) -> None:
        if skip:
            return
        r, g, b = self._color.to_rgb()
        with QSignalBlocker(self._r_spin), QSignalBlocker(self._g_spin), QSignalBlocker(self._b_spin):
            self._r_spin.setValue(r)
            self._g_spin.setValue(g)
            self._b_spin.setValue(b)

    def _refresh_cmy(self, *, skip: bool = False) -> None:
        if skip:
            return
        c, m, y = self._color.to_cmy()
        with QSignalBlocker(self._c_spin), QSignalBlocker(self._m_spin), QSignalBlocker(self._y_spin):
            self._c_spin.setValue(c * 100.0)
            self._m_spin.setValue(m * 100.0)
            self._y_spin.setValue(y * 100.0)

    def _refresh_hex(self, *, skip: bool = False) -> None:
        if skip:
            return
        with QSignalBlocker(self._hex_edit):
            self._hex_edit.setText(str(self._color))

    def _refresh_intensity_slider(self, *, skip: bool = False) -> None:
        if skip:
            return
        with QSignalBlocker(self._intensity_slider):
            self._intensity_slider.setValue(round(self._color.intensity * _INTENSITY_SLIDER_RESOLUTION))

    def _refresh_diagram(self, *, skip: bool = False) -> None:
        if skip:
            self._chromaticity.set_luminance(self._color.intensity)
            return
        self._chromaticity.set_xy(*self._color_to_xy(self._color))
        self._chromaticity.set_luminance(self._color.intensity)

    def _refresh_preview(self) -> None:
        palette = self._preview.palette()
        palette.setColor(QPalette.ColorRole.Window, self._color.to_qt_color())
        self._preview.setPalette(palette)

    # -----------------------------------------------------------------
    # xy ↔ ColorHSI helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _color_to_xy(color: ColorHSI) -> tuple[float, float]:
        """Project a ColorHSI onto CIE xy at its own intensity.

        Fully desaturated or fully black colors fall back to D65, which is
        where the crosshair is placed when no actual chromaticity is defined.
        """
        if color.saturation <= 1e-6 or color.intensity <= 1e-6:
            return cie.D65_WHITE_XY
        r, g, b = color.to_rgb_float()
        linear = (cie.srgb_to_linear_eotf(r), cie.srgb_to_linear_eotf(g), cie.srgb_to_linear_eotf(b))
        xyz = cie.linear_srgb_to_xyz_d65(linear)
        x, y, _ = cie.xyz_to_xyY(xyz)
        return x, y

    def _color_from_xy(self, x: float, y: float) -> ColorHSI:
        """Convert a chromaticity pick into a ``ColorHSI`` without touching the intensity.

        The xy diagram only encodes hue + saturation.  To keep the intensity
        slider stable while picking, we normalize to the pure-hue
        representation (linear max = 1) and then re-apply the current HSV V
        as a straight sRGB multiplier — mirroring what the shader does.

        This intentionally duplicates the shader math instead of calling
        :func:`cie.xy_to_srgb_at_luminance` because that reference helper
        feeds the slider value in as CIE Y, which couples hue/saturation
        picking to CIE luminance.  HSV V (what the picker exposes to the
        caller as ``intensity``) is not CIE Y, so routing picks through the
        reference helper would make dragging the chromaticity marker shift
        the intensity slider — exactly the bug this method exists to avoid.
        See the matching fragment-shader pipeline in
        ``src/resources/shaders/color_picker_chromaticity.frag``.
        """
        xyz = cie.xyY_to_xyz(x, y, 1.0)
        linear = list(cie.xyz_to_linear_srgb_d65(xyz))
        # Clamp negatives (project OOG onto the sRGB boundary).
        linear = [max(0.0, c) for c in linear]
        max_c = max(linear)
        if max_c < 1e-6:
            # Degenerate chromaticity (near-black XYZ); keep the current
            # intensity but drop saturation so we end up at achromatic.
            return ColorHSI(self._color.hue, 0.0, self._color.intensity)
        normalized = tuple(c / max_c for c in linear)
        srgb_at_v1 = cie.linear_srgb_tuple_to_srgb(normalized)
        v = self._color.intensity
        return ColorHSI.from_rgb_float(srgb_at_v1[0] * v, srgb_at_v1[1] * v, srgb_at_v1[2] * v)

    # -----------------------------------------------------------------
    # Slots
    # -----------------------------------------------------------------

    def _on_xy_picked(self, x: float, y: float) -> None:
        if self._updating:
            return
        self._apply_color(self._color_from_xy(x, y), origin="chromaticity")

    def _on_intensity_slider_changed(self, value: int) -> None:
        if self._updating:
            return
        intensity = value / _INTENSITY_SLIDER_RESOLUTION
        self._apply_color(ColorHSI(self._color.hue, self._color.saturation, intensity), origin="intensity_slider")

    def _on_hsi_changed(self, _: float) -> None:
        if self._updating:
            return
        new_color = ColorHSI(self._hue_spin.value(), self._sat_spin.value() / 100.0, self._int_spin.value() / 100.0)
        self._apply_color(new_color, origin="hsi")

    def _on_rgb_changed(self, _: int) -> None:
        if self._updating:
            return
        new_color = ColorHSI.from_rgb(self._r_spin.value(), self._g_spin.value(), self._b_spin.value())
        self._apply_color(new_color, origin="rgb")

    def _on_cmy_changed(self, _: float) -> None:
        if self._updating:
            return
        new_color = ColorHSI.from_cmy(
            self._c_spin.value() / 100.0,
            self._m_spin.value() / 100.0,
            self._y_spin.value() / 100.0,
        )
        self._apply_color(new_color, origin="cmy")

    def _on_hex_edited(self) -> None:
        if self._updating:
            return
        text = self._hex_edit.text().lstrip("#")
        if len(text) != 6:
            # Validator rejects partial input, but editingFinished can still fire
            # with a prefix on focus loss — snap the field back to the model value.
            self._refresh_hex()
            return
        try:
            r = int(text[0:2], 16)
            g = int(text[2:4], 16)
            b = int(text[4:6], 16)
        except ValueError:
            self._refresh_hex()
            return
        self._apply_color(ColorHSI.from_rgb(r, g, b), origin="hex")
