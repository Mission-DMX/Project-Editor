"""Main-menu integration helper for the preset editor dialog.

WP13 only exposes the helper; the actual wiring (which menu to attach to) is
left to WP14. Call ``install_main_menu_entry(main_window)`` from the main
window setup once the integration decision has been made.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow, QWidget


def install_main_menu_entry(main_window: QMainWindow) -> None:
    """Add a "Property-cue presets..." action under the "Edit" or "Tools" menu."""
    menubar = main_window.menuBar()
    target_menu = None
    for action in menubar.actions():
        menu = action.menu()
        if menu is None:
            continue
        title = (menu.title() or "").replace("&", "").strip().lower()
        if title in {"edit", "tools"}:
            target_menu = menu
            break
    if target_menu is None:
        target_menu = menubar.addMenu("Tools")
    action = QAction("Property-cue presets...", main_window)
    action.triggered.connect(lambda _checked=False: _open_dialog(main_window))
    target_menu.addAction(action)


def _open_dialog(parent: QWidget | None) -> None:
    from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
        PresetEditorDialog,
    )
    dialog = PresetEditorDialog(parent=parent)
    dialog.exec()
