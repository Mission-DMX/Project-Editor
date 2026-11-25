"""Headless render-to-PNG visual test for the color picker.

Loads the widget under ``QT_QPA_PLATFORM=offscreen``, drives it through a set
of representative color scenarios, and writes each state to a PNG under
``test/visual_output/color_picker/``.  The PNGs are artifacts — the test is
not pass/fail — but each file is asserted to exist and be non-trivially
sized (> 5 KB) so a gross regression (all-black buffer, broken shader) is
caught in CI.

Run from the ``src/`` directory so ``resource_path`` resolves the shader files:

    cd src
    QT_QPA_PLATFORM=offscreen ../.venv/bin/python ../test/visual_test_color_picker_render.py
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from gl_init import opengl_context_init  # noqa: E402
from model.color_hsi import ColorHSI  # noqa: E402
from view.utility_widgets.color_picker.color_picker_widget import ColorPickerWidget  # noqa: E402

_OUTPUT_DIR = Path(__file__).resolve().parent / "visual_output" / "color_picker"
_MIN_PNG_BYTES = 5 * 1024


def _ensure_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        opengl_context_init()
        QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
        app = QtWidgets.QApplication(sys.argv[:1])
    return app


def _spin(app: QtWidgets.QApplication, widget: QtWidgets.QWidget, ms: int = 250) -> None:
    """Pump the event loop long enough for ``initializeGL`` and the first paint."""
    deadline = QtCore.QDeadlineTimer(ms)
    while not deadline.hasExpired():
        app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 20)
        widget.repaint()


def _save_composite(widget: QtWidgets.QWidget, path: Path) -> None:
    pixmap = widget.grab()
    pixmap.save(str(path), "PNG")


def _save_gl_framebuffer(gl_widget: QtWidgets.QOpenGLWidget, path: Path) -> None:
    img = gl_widget.grabFramebuffer()
    img.save(str(path), "PNG")


def _render(picker: ColorPickerWidget, app: QtWidgets.QApplication) -> None:
    picker.resize(1000, 720)
    picker.show()
    _spin(app, picker, ms=300)


_SCENARIOS: tuple[tuple[str, ColorHSI], ...] = (
    ("default", ColorHSI(0.0, 0.0, 1.0)),
    ("red", ColorHSI.from_rgb(255, 0, 0)),
    ("green", ColorHSI.from_rgb(0, 255, 0)),
    ("blue", ColorHSI.from_rgb(0, 0, 255)),
    ("cyan", ColorHSI.from_rgb(0, 255, 255)),
    ("magenta", ColorHSI.from_rgb(255, 0, 255)),
    ("yellow", ColorHSI.from_rgb(255, 255, 0)),
    ("orange", ColorHSI.from_rgb(255, 128, 32)),
    ("white", ColorHSI(0.0, 0.0, 1.0)),
    ("black", ColorHSI(0.0, 0.0, 0.0)),
    ("low_intensity_green", ColorHSI(120.0, 1.0, 0.3)),
    ("hue_sweep_000", ColorHSI(0.0, 0.8, 1.0)),
    ("hue_sweep_060", ColorHSI(60.0, 0.8, 1.0)),
    ("hue_sweep_120", ColorHSI(120.0, 0.8, 1.0)),
    ("hue_sweep_180", ColorHSI(180.0, 0.8, 1.0)),
    ("hue_sweep_240", ColorHSI(240.0, 0.8, 1.0)),
    ("hue_sweep_300", ColorHSI(300.0, 0.8, 1.0)),
)


class VisualRenderTest(unittest.TestCase):
    """Headless render-to-PNG regression test for the chromaticity color picker."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create the shared QApplication and prepare the output directory."""
        cls.app = _ensure_app()
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def test_render_all_scenarios(self) -> None:
        """Render each scenario to PNG and assert the output file is non-trivially sized."""
        picker = ColorPickerWidget(None)
        _render(picker, self.app)

        for name, color in _SCENARIOS:
            picker.color = color
            _spin(self.app, picker, ms=120)

            composite_path = _OUTPUT_DIR / f"{name}.png"
            gl_path = _OUTPUT_DIR / f"{name}_gl.png"
            _save_composite(picker, composite_path)
            _save_gl_framebuffer(picker._chromaticity, gl_path)  # noqa: SLF001

            self.assertTrue(composite_path.exists(), f"missing {composite_path}")
            self.assertTrue(gl_path.exists(), f"missing {gl_path}")
            self.assertGreater(
                composite_path.stat().st_size,
                _MIN_PNG_BYTES,
                f"composite PNG {composite_path} is suspiciously small",
            )
            self.assertGreater(
                gl_path.stat().st_size,
                1024,
                f"GL PNG {gl_path} is suspiciously small",
            )

        picker.deleteLater()
        self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
