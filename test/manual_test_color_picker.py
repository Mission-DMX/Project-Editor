"""Manual smoke test for ColorPickerWidget.

Run from the ``src/`` directory so ``resource_path`` resolves the shader files.

Manual checklist:
    * Click inside the horseshoe → marker moves, swatch updates, all numeric
      fields re-sync.
    * Drag across the horseshoe → smooth stream of color_changed, no flicker.
    * Type hex ``#FF8020`` → marker jumps, HSI / RGB / CMY all update.
    * R=0, G=255, B=255 → cyan; marker near (0.225, 0.329).
    * Move the intensity slider → diagram brightens/dims live, other fields
      update.
    * Edit Hue alone → RGB rotates, marker traces a radius-like arc in xy.
    * Click outside the horseshoe → marker snaps to nearest locus boundary,
      no NaN, no crash.
    * Resize window → GL viewport reflows, crosshair stays at its mathematical
      xy.
    * Close the window → cleanup runs without error (watch logs).
"""

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

import style
from gl_init import opengl_context_init
from model.color_hsi import ColorHSI
from view.utility_widgets.color_picker.color_picker_widget import ColorPickerWidget

if __name__ == "__main__":
    opengl_context_init()
    QtWidgets.QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])
    app.setStyleSheet(style.APP)

    window = QtWidgets.QMainWindow()
    central = QtWidgets.QWidget(window)
    layout = QVBoxLayout(central)

    picker = ColorPickerWidget(central)
    readout = QLabel("---", central)
    readout.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    def on_color_changed(c: ColorHSI) -> None:
        """Mirror the picker's current color into the readout label and stdout."""
        r, g, b = c.to_rgb()
        readout.setText(
            f"HSI=({c.hue:.1f}°, {c.saturation * 100:.1f}%, {c.intensity * 100:.1f}%)  "
            f"RGB=({r}, {g}, {b})  {c!s}  filter={c.format_for_filter()}"
        )
        print(c.format_for_filter())

    picker.color_changed.connect(on_color_changed)

    layout.addWidget(picker, 1)
    layout.addWidget(readout)
    window.setCentralWidget(central)

    # Programmatic set — should emit color_changed exactly once.
    picker.color = ColorHSI.from_rgb(255, 128, 32)
    # Re-set with the same value — must NOT emit again.
    picker.color = ColorHSI.from_rgb(255, 128, 32)

    window.showMaximized()
    app.exec()
