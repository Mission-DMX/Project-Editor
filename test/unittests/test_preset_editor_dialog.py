"""Unit tests for the WP13 PresetEditorDialog."""

from __future__ import annotations

import gc
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None

_qapp = None


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    gc.enable()


@unittest.skipUnless(_HAS_PYSIDE, "PresetEditorDialog requires PySide6")
class PresetEditorDialogTests(unittest.TestCase):

    def _tmpdir(self) -> Path:
        tmp = tempfile.mkdtemp(prefix="preset_test_")
        self.addCleanup(lambda: _rmtree(Path(tmp)))
        return Path(tmp)

    def test_round_trip(self) -> None:
        from model.virtual_filters.property_cues.presets import PresetHintType, load_preset_library
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog._applies_combo.setCurrentText("dimmer")
        dialog._name_edit.setText("Test")
        dialog._description_edit.setPlainText("Just a tiny preset.")
        dialog._add_hint_row(hint_id="speed", hint_type="float", default="60")
        dialog._add_kf_row(duration_expr="1.0")

        dialog._save()

        file_path = user_dir / "Test.json"
        self.assertTrue(file_path.is_file(), f"expected preset to be written to {file_path}")

        empty_builtin = self._tmpdir()
        library = load_preset_library(builtin_dir=str(empty_builtin), user_dir=str(user_dir))
        self.assertIn("Test", library)
        preset = library["Test"]
        self.assertEqual("dimmer", preset.applies_for)
        self.assertEqual("Test", preset.name)
        self.assertEqual(1, len(preset.hints))
        self.assertEqual("speed", preset.hints[0].id)
        self.assertEqual(PresetHintType.FLOAT, preset.hints[0].type)

        self.assertIsNotNone(dialog.result_preset())
        self.assertEqual("Test", dialog.result_preset().name)

    def test_builtin_opened_saves_to_user(self) -> None:
        from model.virtual_filters.property_cues.presets import (
            EffectPreset,
            PresetHintSpec,
            PresetHintType,
            PresetKeyFrameEntry,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        builtin_dir = self._tmpdir()
        builtin_path = builtin_dir / "ShippedPreset.json"
        builtin_path.write_text("{\"original\": true}", encoding="utf-8")
        shipped_bytes = builtin_path.read_bytes()

        shipped = EffectPreset(
            name="Shipped",
            description="Shipped",
            applies_for="position",
            hints=(PresetHintSpec(id="speed", type=PresetHintType.FLOAT, default=60),),
            kf_requests=(PresetKeyFrameEntry(duration_expr="1.0", channel_exprs={"pan_value": "0"}),),
            source_path=str(builtin_path),
            is_builtin=True,
        )

        dialog = PresetEditorDialog(existing=shipped, user_dir=user_dir)
        dialog._name_edit.setText("Test2")

        dialog._save()

        self.assertTrue((user_dir / "Test2.json").is_file())
        self.assertFalse((user_dir / "Shipped.json").is_file())
        self.assertEqual(shipped_bytes, builtin_path.read_bytes(), "built-in preset must not be modified")

    def test_validation_failure_shows_msgbox(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog._applies_combo.setCurrentText("dimmer")
        dialog._name_edit.setText("")

        self.assertFalse(dialog.isVisible())
        dialog._save()

        self.assertIsNotNone(dialog._msgbox, "a QMessageBox should have been stored on the dialog")
        from PySide6.QtWidgets import QMessageBox
        self.assertIsInstance(dialog._msgbox, QMessageBox)
        self.assertEqual([], list(user_dir.glob("*.json")))
        self.assertIsNone(dialog.result_preset())
        self.assertEqual(QMessageBox.Icon.Warning, dialog._msgbox.icon())

    def test_cancel_returns_none(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog.reject()
        self.assertIsNone(dialog.result_preset())

    def test_dialog_lists_applicable_properties(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        items = [dialog._applies_combo.itemText(i) for i in range(dialog._applies_combo.count())]
        for expected in ("dimmer", "position", "colour"):
            self.assertIn(expected, items)

    def test_keyframe_entry_round_trips(self) -> None:
        from model.virtual_filters.property_cues.presets import load_preset_library
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog._applies_combo.setCurrentText("position")
        dialog._name_edit.setText("Posed")
        dialog._add_kf_row(
            duration_expr="2.5",
            channel_exprs={
                "pan_value": "42",
                "pan_curvesel": "1",
                "tilt_value": "17",
                "tilt_curvesel": "2",
            },
        )

        dialog._save()

        empty_builtin = self._tmpdir()
        library = load_preset_library(builtin_dir=str(empty_builtin), user_dir=str(user_dir))
        preset = library["Posed"]
        self.assertEqual(1, len(preset.kf_requests))
        entry = preset.kf_requests[0]
        self.assertEqual("2.5", entry.duration_expr)
        self.assertEqual("42", entry.channel_exprs["pan_value"])
        self.assertEqual("17", entry.channel_exprs["tilt_value"])


def _rmtree(path: Path) -> None:
    import shutil
    try:
        shutil.rmtree(path)
    except OSError:
        pass


if __name__ == "__main__":
    unittest.main()
