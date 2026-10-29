"""Unit tests for the effect-preset format, loader, and evaluator (WP5)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from model.color_hsi import ColorHSI
from model.virtual_filters.property_cues.presets import (
    EffectPreset,
    PresetHintSpec,
    PresetHintType,
    PresetKeyFrameEntry,
    evaluate_preset,
    load_preset_library,
)
from model.virtual_filters.property_cues.presets.schema import validate


_CIRCLE_USER_BLOB = {
    "name": "Circle",
    "description": "User override of circle.",
    "applies_for": "position",
    "hints": [
        {"id": "speed", "type": "float", "default": 42},
        {"id": "size", "type": "float", "default": 1},
    ],
    "kf_requests": [
        {"duration": "{{ speed }}", "channels": {"pan_value": "0.0"}},
    ],
}


class PresetLoaderTest(unittest.TestCase):
    """Loading and precedence of built-in and user presets."""

    def test_builtin_presets_load(self) -> None:
        library = load_preset_library()
        self.assertIn("Circle", library)
        self.assertTrue(library["Circle"].is_builtin)
        self.assertEqual("position", library["Circle"].applies_for)
        self.assertEqual(4, len(library["Circle"].kf_requests))

    def test_user_shadows_builtin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            user_dir = Path(tmp)
            (user_dir / "circle.json").write_text(json.dumps(_CIRCLE_USER_BLOB), encoding="utf-8")
            library = load_preset_library(user_dir=str(user_dir))
            self.assertIn("Circle", library)
            self.assertFalse(library["Circle"].is_builtin)
            self.assertEqual("User override of circle.", library["Circle"].description)

    def test_malformed_file_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            builtin_dir = Path(tmp)
            valid_blob = {
                "name": "Pulse",
                "description": "",
                "applies_for": "dimmer",
                "hints": [],
                "kf_requests": [
                    {"duration": "0.5", "channels": {"brightness": "255"}},
                ],
            }
            (builtin_dir / "pulse.json").write_text(json.dumps(valid_blob), encoding="utf-8")
            (builtin_dir / "broken.json").write_text("{{{", encoding="utf-8")
            with tempfile.TemporaryDirectory() as empty_user_dir:
                library = load_preset_library(
                    builtin_dir=str(builtin_dir), user_dir=empty_user_dir
                )
            self.assertEqual({"Pulse"}, set(library.keys()))


class PresetEvaluatorTest(unittest.TestCase):
    """Evaluating preset kf-requests into keyframe request streams."""

    def _circle_preset(self) -> EffectPreset:
        library = load_preset_library()
        return library["Circle"]

    def test_evaluate_circle(self) -> None:
        preset = self._circle_preset()
        requests = evaluate_preset(
            preset=preset,
            hint_values={"speed": 0.5, "size": 1},
            step_start_40hz=0,
            step_duration_40hz=80,
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        self.assertEqual([0, 20, 40, 60], [req.timestep_40hz for req in pan_value])
        # Entry 2 in the spec (1-based) corresponds to index 1 in the emitted list.
        self.assertAlmostEqual(128.0, float(pan_value[1].requested_value))

    def test_evaluate_truncates(self) -> None:
        preset = self._circle_preset()
        requests = evaluate_preset(
            preset=preset,
            hint_values={"speed": 0.5, "size": 1},
            step_start_40hz=0,
            step_duration_40hz=30,
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        self.assertEqual(2, len(pan_value))
        self.assertEqual([0, 20], [req.timestep_40hz for req in pan_value])

    def test_evaluate_repeats(self) -> None:
        preset = self._circle_preset()
        requests = evaluate_preset(
            preset=preset,
            hint_values={"speed": 0.5, "size": 1},
            step_start_40hz=0,
            step_duration_40hz=200,
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        self.assertEqual(10, len(pan_value))
        self.assertEqual(0, pan_value[0].timestep_40hz)
        self.assertEqual(180, pan_value[-1].timestep_40hz)

    def test_color_hint_rendering(self) -> None:
        preset = EffectPreset(
            name="ColorBlink",
            description="",
            applies_for="colour",
            hints=(
                PresetHintSpec(
                    id="start_color",
                    type=PresetHintType.COLOR,
                    default="120.0,1.0,0.5",
                ),
            ),
            kf_requests=(
                PresetKeyFrameEntry(duration_expr="1.0", channel_exprs={"color": "{{ start_color }}"}),
            ),
            source_path="",
            is_builtin=False,
        )
        requests = evaluate_preset(
            preset=preset,
            hint_values={},
            step_start_40hz=5,
            step_duration_40hz=40,
            per_child_delay_seconds=0.0,
        )
        color_requests = requests["color"]
        self.assertEqual(1, len(color_requests))
        value = color_requests[0].requested_value
        self.assertIsInstance(value, ColorHSI)
        self.assertAlmostEqual(120.0, value.hue)
        self.assertAlmostEqual(1.0, value.saturation)
        self.assertAlmostEqual(0.5, value.intensity)
        self.assertEqual(5, color_requests[0].timestep_40hz)


class PresetSchemaTest(unittest.TestCase):
    """Hand-written validator for the preset JSON schema."""

    def test_schema_validate_pass_fail(self) -> None:
        good = {
            "name": "Pulse",
            "description": "",
            "applies_for": "dimmer",
            "hints": [{"id": "x", "type": "float", "default": 1}],
            "kf_requests": [
                {"duration": "1.0", "channels": {"brightness": "255"}},
            ],
        }
        self.assertEqual([], validate(good))
        bad = {
            "name": "Pulse",
            "kf_requests": [
                {"duration": "1.0", "channels": {"brightness": "255"}},
            ],
        }
        errors = validate(bad)
        self.assertTrue(any("applies_for" in message for message in errors))


if __name__ == "__main__":
    unittest.main()
