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
    """Spin up a shared QApplication and disable GC for the preset-dialog tests."""
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable Python's garbage collector after the preset-dialog tests."""
    gc.enable()


@unittest.skipUnless(_HAS_PYSIDE, "PresetEditorDialog requires PySide6")
class PresetEditorDialogTests(unittest.TestCase):
    """Verify PresetEditorDialog save flow, data loss guards and preset listing."""

    def _tmpdir(self) -> Path:
        """Create a scoped temporary directory and schedule its cleanup."""
        tmp = tempfile.mkdtemp(prefix="preset_test_")
        self.addCleanup(lambda: _rmtree(Path(tmp)))
        return Path(tmp)

    def test_round_trip(self) -> None:
        """Verify saving a new preset writes JSON and round-trips through the library loader."""
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
        """Verify editing a built-in preset writes a copy to the user dir and leaves the shipped file intact."""
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
        """Verify an invalid preset name shows a warning QMessageBox and writes no file."""
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
        """Verify rejecting the dialog yields a None result preset."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog.reject()
        self.assertIsNone(dialog.result_preset())

    def test_dialog_lists_applicable_properties(self) -> None:
        """Verify the applies-to combo lists the expected property targets."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )

        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        items = [dialog._applies_combo.itemText(i) for i in range(dialog._applies_combo.count())]
        for expected in ("dimmer", "position", "color"):
            self.assertIn(expected, items)

    def test_keyframe_entry_round_trips(self) -> None:
        """Verify a keyframe entry with channel expressions round-trips through save and load."""
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


    def test_dimmer_channels_match_compiler(self) -> None:
        """Regression: the dialog's dimmer channel list must match what the compiler emits.

        Before L12 the dialog listed ``brightness`` but the compiler's raw
        name is ``brightness_raw``; the resulting preset compiled to a
        constant brightness of 0 because ``brightness`` never showed up in
        the solver's channel set.
        """
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            _PROPERTY_CHANNELS,
        )
        dimmer_channels = _PROPERTY_CHANNELS["dimmer"]
        self.assertIn("brightness_raw", dimmer_channels)
        self.assertNotIn("brightness", dimmer_channels)

    def test_beam_channels_no_focus_include_prism(self) -> None:
        """Regression: beam channel list reflects BeamProperty (no focus; prism present)."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            _PROPERTY_CHANNELS,
        )
        beam = _PROPERTY_CHANNELS["beam"]
        self.assertNotIn("focus", beam)
        self.assertIn("prism_selection", beam)
        self.assertIn("prism_rotation", beam)

    def test_filename_sanitisation_round_trips(self) -> None:
        """Regression: names with spaces or unsafe chars get a safe filename."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )
        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog._applies_combo.setCurrentText("dimmer")
        dialog._name_edit.setText("Hero Spot / foo")
        dialog._save()
        files = sorted(p.name for p in user_dir.glob("*.json"))
        self.assertEqual(1, len(files), f"Expected one preset file, got {files}")
        for ch in (" ", "/", "\\", ":"):
            self.assertNotIn(ch, files[0])

    def test_rename_in_user_dir_deletes_old_file(self) -> None:
        """Regression: renaming a user preset drops the old JSON file."""
        from model.virtual_filters.property_cues.presets import load_preset_library
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )
        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog._applies_combo.setCurrentText("dimmer")
        dialog._name_edit.setText("OriginalName")
        dialog._save()
        self.assertTrue((user_dir / "OriginalName.json").is_file())

        # Reload the preset and open it for editing.
        empty_builtin = self._tmpdir()
        library = load_preset_library(builtin_dir=str(empty_builtin), user_dir=str(user_dir))
        preset = library["OriginalName"]
        dialog2 = PresetEditorDialog(existing=preset, user_dir=user_dir)
        dialog2._name_edit.setText("Renamed")
        dialog2._save()

        files = sorted(p.name for p in user_dir.glob("*.json"))
        self.assertEqual(["Renamed.json"], files,
                         f"Expected only the renamed file; got {files}")

    def test_applies_for_change_preserves_channel_exprs(self) -> None:
        """Regression: switching applies_for back and forth preserves per-channel values."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )
        user_dir = self._tmpdir()
        dialog = PresetEditorDialog(user_dir=user_dir)
        dialog._applies_combo.setCurrentText("position")
        dialog._add_kf_row(
            duration_expr="1.0",
            channel_exprs={"pan_value": "42", "tilt_value": "17"},
        )
        # Switch to a different applies_for and back.
        dialog._applies_combo.setCurrentText("dimmer")
        dialog._applies_combo.setCurrentText("position")
        # The pan_value and tilt_value expressions must still be in place
        # because they live in the passthrough map when position's columns
        # are rebuilt.
        self.assertEqual(1, dialog._kf_table.rowCount())
        exprs = dialog._collect_kf_blob()
        self.assertIn("pan_value", exprs[0]["channels"])
        self.assertIn("tilt_value", exprs[0]["channels"])
        self.assertEqual("42", exprs[0]["channels"]["pan_value"])
        self.assertEqual("17", exprs[0]["channels"]["tilt_value"])

    def test_color_hint_default_preserved_on_round_trip(self) -> None:
        """Regression: colour hint defaults are preserved as the ``"H,S,I"`` string."""
        from model.virtual_filters.property_cues.presets import (
            EffectPreset,
            PresetHintSpec,
            PresetHintType,
            PresetKeyFrameEntry,
            load_preset_library,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preset_editor.dialog import (
            PresetEditorDialog,
        )
        user_dir = self._tmpdir()
        existing = EffectPreset(
            name="ColorHintPreset",
            description="Carries a colour hint",
            applies_for="color",
            hints=(PresetHintSpec(id="start_color", type=PresetHintType.COLOR, default="120.0,1.0,1.0"),),
            kf_requests=(PresetKeyFrameEntry(duration_expr="1.0", channel_exprs={"color": "{{start_color}}"}),),
            source_path=str(user_dir / "ColorHintPreset.json"),
            is_builtin=False,
        )
        # Pre-seed the file so the library loader can find it after rewrite.
        (user_dir / "ColorHintPreset.json").write_text("{}", encoding="utf-8")

        dialog = PresetEditorDialog(existing=existing, user_dir=user_dir)
        dialog._save()

        empty_builtin = self._tmpdir()
        library = load_preset_library(builtin_dir=str(empty_builtin), user_dir=str(user_dir))
        reloaded = library["ColorHintPreset"]
        self.assertEqual(1, len(reloaded.hints))
        self.assertEqual(PresetHintType.COLOR, reloaded.hints[0].type)
        self.assertEqual("120.0,1.0,1.0", reloaded.hints[0].default)


def _rmtree(path: Path) -> None:
    import shutil
    try:
        shutil.rmtree(path)
    except OSError:
        pass


if __name__ == "__main__":
    unittest.main()
