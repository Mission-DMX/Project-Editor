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
        """Verify the built-in presets (Circle, sweeps, Color Change) are available in the library."""
        library = load_preset_library()
        self.assertIn("Circle", library)
        self.assertTrue(library["Circle"].is_builtin)
        self.assertEqual("position", library["Circle"].applies_for)
        self.assertEqual(16, len(library["Circle"].kf_requests))
        # Sweep + colour-change presets ship alongside Circle.
        for name in ("Pan Sweep", "Tilt Sweep", "Color Change"):
            self.assertIn(name, library, f"built-in preset {name!r} not loaded")
            self.assertTrue(library[name].is_builtin)
        self.assertEqual("position", library["Pan Sweep"].applies_for)
        self.assertEqual("position", library["Tilt Sweep"].applies_for)
        self.assertEqual("color", library["Color Change"].applies_for)

    def test_user_shadows_builtin(self) -> None:
        """Verify a user preset with the same name shadows its built-in counterpart."""
        with tempfile.TemporaryDirectory() as tmp:
            user_dir = Path(tmp)
            (user_dir / "circle.json").write_text(json.dumps(_CIRCLE_USER_BLOB), encoding="utf-8")
            library = load_preset_library(user_dir=str(user_dir))
            self.assertIn("Circle", library)
            self.assertFalse(library["Circle"].is_builtin)
            self.assertEqual("User override of circle.", library["Circle"].description)

    def test_malformed_file_skipped(self) -> None:
        """Verify a malformed preset file is skipped without blocking valid presets from loading."""
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

    # The Circle preset ships with 16 keyframes per full rotation. ``seconds``
    # controls one full revolution; with ``seconds=12.8`` each keyframe is
    # 0.8 s = 32 40-Hz ticks and the expected timesteps are integer multiples
    # of 32 -- convenient for assertions.
    _CIRCLE_HINTS = {
        "seconds": 12.8,
        "size": 1,
        "distance": 10,
        "pan_range_deg": 540,
        "tilt_range_deg": 270,
    }

    def test_evaluate_circle(self) -> None:
        """Verify evaluating the Circle preset yields the expected pan/tilt keyframe stream."""
        preset = self._circle_preset()
        requests = evaluate_preset(
            preset=preset,
            hint_values=self._CIRCLE_HINTS,
            step_start_40hz=0,
            step_duration_40hz=512,  # one full circle
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        tilt_value = requests["tilt_value"]
        self.assertEqual(16, len(pan_value))
        self.assertEqual(
            [i * 32 for i in range(16)],
            [req.timestep_40hz for req in pan_value],
        )
        # size=1 at distance=10, pan_range=540° → amp_pan = 1*57.2958/(10*540).
        amp_pan = 1 * 57.2958 / (10 * 540)
        amp_tilt = 1 * 57.2958 / (10 * 270)
        # Angle 0: pan = centre + amp, tilt = centre.
        self.assertAlmostEqual(0.5 + amp_pan, float(pan_value[0].requested_value), places=4)
        self.assertAlmostEqual(0.5, float(tilt_value[0].requested_value), places=4)
        # Angle π/2 (i=4): pan centre, tilt centre + amp_tilt.
        self.assertAlmostEqual(0.5, float(pan_value[4].requested_value), places=4)
        self.assertAlmostEqual(0.5 + amp_tilt, float(tilt_value[4].requested_value), places=4)

    def test_evaluate_truncates(self) -> None:
        """Verify evaluating truncates the keyframe stream when the step duration ends mid-pattern."""
        preset = self._circle_preset()
        # 100 ticks = 2.5 s = four full keyframes at 0, 32, 64, 96.
        requests = evaluate_preset(
            preset=preset,
            hint_values=self._CIRCLE_HINTS,
            step_start_40hz=0,
            step_duration_40hz=100,
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        self.assertEqual(4, len(pan_value))
        self.assertEqual([0, 32, 64, 96], [req.timestep_40hz for req in pan_value])

    def test_evaluate_repeats(self) -> None:
        """Verify evaluating repeats the preset keyframe stream across multiple rotations."""
        preset = self._circle_preset()
        # 1024 ticks = 25.6 s = two full rotations → 32 keyframes.
        requests = evaluate_preset(
            preset=preset,
            hint_values=self._CIRCLE_HINTS,
            step_start_40hz=0,
            step_duration_40hz=1024,
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        self.assertEqual(32, len(pan_value))
        self.assertEqual(0, pan_value[0].timestep_40hz)
        self.assertEqual(31 * 32, pan_value[-1].timestep_40hz)

    def test_circle_clamps_oversized_projection(self) -> None:
        """A circle larger than the fixture's range gets clamped to half-range.

        Requesting a huge circle (``size=1000`` at ``distance=10``) would need
        more pan/tilt travel than the fixture physically has. The preset uses
        ``min(size*57.3/distance, pan_range/2, tilt_range/2)`` so both axes
        clamp to the tighter axis' half-range (tilt = 135°), keeping the shape
        a true circle rather than letting one axis hit the hard stop.
        """
        preset = self._circle_preset()
        hints = dict(self._CIRCLE_HINTS)
        hints["size"] = 1000
        requests = evaluate_preset(
            preset=preset,
            hint_values=hints,
            step_start_40hz=0,
            step_duration_40hz=512,
            per_child_delay_seconds=0.0,
        )
        pan_value = requests["pan_value"]
        tilt_value = requests["tilt_value"]
        # Clamped angular half-amplitude = tilt_range/2 = 135°. On tilt that's
        # 0.5 of the DMX range; on pan (540°) it's 135/540 = 0.25.
        self.assertAlmostEqual(0.5 + 0.25, float(pan_value[0].requested_value), places=4)
        self.assertAlmostEqual(0.5, float(tilt_value[0].requested_value), places=4)
        # Quarter-turn: pan centred, tilt fully extended (0.5 + 0.5 = 1.0).
        self.assertAlmostEqual(0.5, float(pan_value[4].requested_value), places=4)
        self.assertAlmostEqual(1.0, float(tilt_value[4].requested_value), places=4)

    def test_color_hint_rendering(self) -> None:
        """Verify rendering a colour hint produces a ColorHSI keyframe value."""
        preset = EffectPreset(
            name="ColorBlink",
            description="",
            applies_for="color",
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


class PresetLibraryCacheTest(unittest.TestCase):
    """the module-level preset cache must be returned on subsequent calls."""

    def test_default_invocation_is_cached(self) -> None:
        """Verify ``load_preset_library()`` returns the same object on repeat calls."""
        from model.virtual_filters.property_cues.presets import (
            load_preset_library,
            reload_preset_library,
        )
        reload_preset_library()
        first = load_preset_library()
        second = load_preset_library()
        self.assertIs(first, second)
        reload_preset_library()
        third = load_preset_library()
        self.assertIsNot(first, third,
                         "reload_preset_library must drop the cache so the next call rebuilds")

    def test_custom_dir_bypasses_cache(self) -> None:
        """Verify passing a custom dir does not return the cached default library."""
        from model.virtual_filters.property_cues.presets import load_preset_library
        with tempfile.TemporaryDirectory() as tmp:
            empty = load_preset_library(builtin_dir=tmp, user_dir=tmp)
            self.assertEqual({}, empty)


class PresetTemplateCacheTest(unittest.TestCase):
    """Jinja template compilations must be cached across evaluations."""

    def test_template_cache_reuses_compiled_templates(self) -> None:
        """Verify evaluating the same expression twice returns the same compiled template."""
        from model.virtual_filters.property_cues.presets.evaluator import (
            _TEMPLATE_CACHE,
            _compile_template,
            clear_template_cache,
        )
        from controller.utils.jinja_math import get_math_enabled_jinja_env

        clear_template_cache()
        env = get_math_enabled_jinja_env()
        a = _compile_template(env, "{{ x }}")
        b = _compile_template(env, "{{ x }}")
        self.assertIs(a, b)
        self.assertIn("{{ x }}", _TEMPLATE_CACHE)
        clear_template_cache()
        self.assertNotIn("{{ x }}", _TEMPLATE_CACHE)


class PresetHintValidationTest(unittest.TestCase):
    """unknown hints must be tolerated; min/max must be enforced."""

    def _dimmer_preset(self, hints: tuple[PresetHintSpec, ...]) -> EffectPreset:
        return EffectPreset(
            name="P", description="", applies_for="dimmer", hints=hints,
            kf_requests=(
                PresetKeyFrameEntry(
                    duration_expr="1.0",
                    channel_exprs={"brightness_raw": "{{ speed }}"},
                ),
            ),
            source_path="",
            is_builtin=False,
        )

    def test_unknown_hint_is_warning_not_error(self) -> None:
        """Regression: unknown hint ids are dropped with a warning (not raised)."""
        preset = self._dimmer_preset(
            hints=(PresetHintSpec(id="speed", type=PresetHintType.FLOAT, default=0.5),),
        )
        # Provided hints include a renamed/removed id -- evaluation should
        # still succeed using the known hint's default.
        result = evaluate_preset(
            preset, {"speed": 0.3, "legacy_removed": 1.0},
            step_start_40hz=0, step_duration_40hz=40, per_child_delay_seconds=0.0,
        )
        self.assertIn("brightness_raw", result)
        self.assertEqual(0.3, float(result["brightness_raw"][0].requested_value))

    def test_min_max_clamp_numeric_hint(self) -> None:
        """Regression: numeric hint values outside [min, max] are clamped."""
        preset = self._dimmer_preset(
            hints=(PresetHintSpec(
                id="speed", type=PresetHintType.FLOAT,
                default=0.5, minimum=0.0, maximum=1.0,
            ),),
        )
        result = evaluate_preset(
            preset, {"speed": 999.0},
            step_start_40hz=0, step_duration_40hz=40, per_child_delay_seconds=0.0,
        )
        # Clamped to maximum=1.0.
        self.assertEqual(1.0, float(result["brightness_raw"][0].requested_value))

        result_neg = evaluate_preset(
            preset, {"speed": -2.0},
            step_start_40hz=0, step_duration_40hz=40, per_child_delay_seconds=0.0,
        )
        self.assertEqual(0.0, float(result_neg["brightness_raw"][0].requested_value))

    def test_int_hint_clamped_and_rounded(self) -> None:
        """Regression: int hints respect min/max and are coerced to int."""
        preset = EffectPreset(
            name="P", description="", applies_for="gobo",
            hints=(PresetHintSpec(
                id="wheel", type=PresetHintType.INT, default=0,
                minimum=0, maximum=5,
            ),),
            kf_requests=(
                PresetKeyFrameEntry(
                    duration_expr="1.0",
                    channel_exprs={"goboslot_0": "{{ wheel }}"},
                ),
            ),
            source_path="",
            is_builtin=False,
        )
        result = evaluate_preset(
            preset, {"wheel": 42.7},
            step_start_40hz=0, step_duration_40hz=40, per_child_delay_seconds=0.0,
        )
        # Clamped to max=5, coerced to int.
        self.assertEqual(5.0, float(result["goboslot_0"][0].requested_value))


class PresetSchemaTest(unittest.TestCase):
    """Hand-written validator for the preset JSON schema."""

    def test_schema_validate_pass_fail(self) -> None:
        """Verify the schema validator accepts well-formed presets and reports missing fields."""
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
