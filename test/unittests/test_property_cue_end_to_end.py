"""End-to-end integration test for the property-based cue vfilter (WP14).

Run from ``src``: ``python -m unittest test.unittests.test_property_cue_end_to_end``.
"""

from __future__ import annotations

import gc
import importlib.util
import sys
import time
import unittest
from logging import getLogger
from typing import Any
from unittest.mock import patch

logger = getLogger(__name__)

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None

_qapp = None


def setUpModule() -> None:  # noqa: N802 - unittest hook
    """Create a shared QApplication and disable the GC for the duration of the tests."""
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 - unittest hook
    """Re-enable garbage collection after the module-level tests have finished."""
    gc.enable()


def _make_scene():
    """Return a BoardConfiguration and its freshly added Scene for e2e property-cue tests."""
    from model import BoardConfiguration, Scene
    show = BoardConfiguration()
    scene = Scene(0, "Test property-cue e2e scene", show)
    show._add_scene(scene)
    return show, scene


def _manual_dimmer(brightness: float):
    from model.virtual_filters.property_cues.model import (
        ManualPropertyAssignment,
        PropertyAssignments,
    )
    return PropertyAssignments(
        by_property={
            "dimmer": ManualPropertyAssignment(
                values={"brightness": brightness, "strobefreq": 0.0},
            ),
        },
    )


def _manual_position(pan: float, tilt: float):
    from model.virtual_filters.property_cues.model import (
        ManualPropertyAssignment,
        PropertyAssignments,
    )
    return PropertyAssignments(
        by_property={
            "position": ManualPropertyAssignment(
                values={
                    "pan_value": pan,
                    "pan_curvesel": 0,
                    "tilt_value": tilt,
                    "tilt_curvesel": 0,
                },
            ),
        },
    )


def _preset_position(preset_id: str, hints: dict[str, Any] | None = None):
    from model.virtual_filters.property_cues.model import (
        PresetPropertyAssignment,
        PropertyAssignments,
    )
    return PropertyAssignments(
        by_property={
            "position": PresetPropertyAssignment(
                preset_id=preset_id,
                hint_values=hints or {},
            ),
        },
    )


def _build_populated_filter(scene):
    from model.filter import FilterTypeEnumeration
    from model.filters.factory import construct_filter_instance
    from model.virtual_filters.property_cues.model import (
        EnabledCapability,
        FixtureSelection,
        FixtureSelectionEntry,
        PropertyCue,
        PropertyStep,
        SelectionEntryKind,
    )
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

    vfilter = construct_filter_instance(
        scene=scene,
        filter_type=int(FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES),
        filter_id="pcf_e2e",
    )
    assert isinstance(vfilter, PropertyBasedCueFilter)
    vfilter.property_model.fixture_selection = FixtureSelection(
        entries=[
            FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1"),
            FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH2"),
        ],
        enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.POSITION},
    )
    cue1 = PropertyCue(name="Cue 1", steps=[
        PropertyStep(name="s0", duration_40hz=40, assignments={
            "fixture:MH1": _manual_dimmer(1.0),
            "fixture:MH2": _manual_dimmer(0.75),
        }),
    ])
    cue2 = PropertyCue(name="Cue 2", steps=[
        PropertyStep(name="s0", duration_40hz=80, assignments={
            "fixture:MH1": _preset_position(
                "Circle",
                {
                    "seconds": 40.0,
                    "size": 1.0,
                    "distance": 10.0,
                    "pan_range_deg": 540.0,
                    "tilt_range_deg": 270.0,
                },
            ),
            "fixture:MH2": _manual_position(0.5, 0.75),
        }),
    ])
    vfilter.property_model.cues.append(cue1)
    vfilter.property_model.cues.append(cue2)
    return vfilter


@unittest.skipUnless(_HAS_PYSIDE, "Property cue vfilter requires PySide6")
class PropertyCueEndToEndTests(unittest.TestCase):
    """End-to-end integration tests covering the property-based cue pipeline."""

    def setUp(self) -> None:
        """Build a scene and a populated property-based cue filter for each test."""
        self.show, self.scene = _make_scene()
        self.vfilter = _build_populated_filter(self.scene)

    def test_full_pipeline_dimmer_position_preset(self) -> None:
        """Verify compiling produces native channels, post-process filters, and strobe outputs."""
        from model.filter import FilterTypeEnumeration

        res = self.vfilter._ensure_compiled()
        native_channels = {name for name, _dt in res.native_model.channels}
        # The native cue filter emits ``brightness_raw`` (not ``brightness``):
        # the strobe post-process strategy publishes ``brightness`` externally,
        # and distinct raw/exposed names prevent the serializer's override
        # dictionary from rewriting the strobe filter's own input onto its
        # own output.
        # ``brightness_raw`` / ``pan_value`` / ``tilt_value`` differ per fixture
        # (MH1 is on a circle, MH2 sits at 0.5/0.75; MH1 is at brightness 1.0,
        # MH2 at 0.75) so neither pair consolidates and both fixtures keep
        # their own channel.
        for ch in ("MH1__brightness_raw", "MH2__brightness_raw",
                   "MH1__pan_value", "MH2__pan_value",
                   "MH1__tilt_value", "MH2__tilt_value"):
            self.assertIn(ch, native_channels, f"missing native channel: {ch}")
        # The Circle preset selects raw passthrough (``curvesel=0``) and the
        # manual MH2 assignment does the same, so the two fixtures share the
        # same constant curvesel stream and the consolidator collapses them
        # onto a single canonical channel per axis.
        self.assertTrue(
            any(ch.endswith("__pan_curvesel") for ch in native_channels),
            f"expected at least one pan_curvesel channel, got {sorted(native_channels)}",
        )
        self.assertTrue(
            any(ch.endswith("__tilt_curvesel") for ch in native_channels),
            f"expected at least one tilt_curvesel channel, got {sorted(native_channels)}",
        )

        resolved_pan = self.vfilter.resolve_output_port_id("MH1__pan")
        self.assertIsNotNone(resolved_pan)
        self.assertTrue(
            resolved_pan.endswith("pan_range:value"),
            f"pan output port must come from the 16-bit adapter, got: {resolved_pan}",
        )

        ids_by_type: dict[int, list[str]] = {}
        for f in res.postprocess_filters:
            ids_by_type.setdefault(int(f.filter_type), []).append(f.filter_id)
        for required in (
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN,
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN,
            FilterTypeEnumeration.FILTER_SWITCH_FLOAT,
            FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE,
        ):
            self.assertGreaterEqual(
                len(ids_by_type.get(int(required), [])), 4,
                f"expected at least 4 filters of type {required.name} "
                f"(pan+tilt for 2 fixtures), got: {ids_by_type.get(int(required))}",
            )

        range_filter = next(
            f for f in res.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE)
            and f.filter_id.endswith("MH1__pan_range")
        )
        self.assertTrue(range_filter.channel_links["value_in"].endswith(":out"))

        strobe_filters = [
            f for f in res.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
        ]
        self.assertEqual(2, len(strobe_filters),
                         "expected one float strobe generator per fixture")
        resolved_brightness = self.vfilter.resolve_output_port_id("MH1__brightness")
        self.assertIsNotNone(resolved_brightness)
        self.assertTrue(
            resolved_brightness.endswith("_dimmer_strobe:value"),
            f"brightness output port must come from strobe generator, got: {resolved_brightness}",
        )

    def test_serialize_deserialize_roundtrip(self) -> None:
        """Verify serializing and deserializing the vfilter preserves all cues and assignments."""
        from model.virtual_filters.property_cues.model import (
            ManualPropertyAssignment,
            PresetPropertyAssignment,
        )
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        self.vfilter.serialize()
        payload = self.vfilter.filter_configurations["cues-prop-data"]
        self.assertNotEqual("", payload)

        fresh = PropertyBasedCueFilter(self.scene, "pcf_e2e_reload")
        fresh.filter_configurations["cues-prop-data"] = payload
        fresh.deserialize()

        self.assertEqual(len(self.vfilter.property_model.cues),
                         len(fresh.property_model.cues))
        for a, b in zip(self.vfilter.property_model.cues,
                        fresh.property_model.cues, strict=True):
            self.assertEqual(a.name, b.name)
            self.assertEqual(len(a.steps), len(b.steps))
            for sa, sb in zip(a.steps, b.steps, strict=True):
                self.assertEqual(sa.duration_40hz, sb.duration_40hz)
                self.assertEqual(set(sa.assignments.keys()),
                                 set(sb.assignments.keys()))
                for node_path, assigns in sa.assignments.items():
                    other = sb.assignments[node_path]
                    self.assertEqual(set(assigns.by_property.keys()),
                                     set(other.by_property.keys()))
                    for pid, orig in assigns.by_property.items():
                        rt = other.by_property[pid]
                        self.assertIs(type(orig), type(rt))
                        if isinstance(orig, ManualPropertyAssignment):
                            self.assertEqual(orig.values, rt.values)
                        elif isinstance(orig, PresetPropertyAssignment):
                            self.assertEqual(orig.preset_id, rt.preset_id)
                            self.assertEqual(orig.hint_values, rt.hint_values)

    def test_consolidation(self) -> None:
        """Verify identical per-fixture dimmer timelines consolidate onto a single strobe generator."""
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            PropertyCue,
            PropertyStep,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        vfilter = PropertyBasedCueFilter(self.scene, "pcf_cons_e2e")
        vfilter.property_model.fixture_selection = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH2"),
            ],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        vfilter.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40, assignments={
                "fixture:MH1": _manual_dimmer(0.5),
                "fixture:MH2": _manual_dimmer(0.5),
            }),
        ]))
        res = vfilter._ensure_compiled()
        a = vfilter.resolve_output_port_id("MH1__brightness")
        b = vfilter.resolve_output_port_id("MH2__brightness")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        # Both fixtures share identical dimmer timelines so the consolidator
        # collapses them to the MH1 canonical channel on the native cue filter;
        # the dimmer strategy therefore builds a single float strobe generator
        # with the MH1 prefix which supplies the gated brightness.
        strobes = [
            f for f in res.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
        ]
        self.assertEqual(1, len(strobes),
                         "consolidated brightness should drive a single strobe generator")

    def test_preview_thread_tick_for_cue(self) -> None:
        """Verify the preview thread ticks and routes updates into the preview constant filters."""
        from model.virtual_filters.property_cues import preview_runtime
        from model.virtual_filters.property_cues.preview_runtime import (
            PropertyCuesPreviewThread,
            build_preview_filters,
        )

        collected: list = []
        mapping = build_preview_filters(self.vfilter, self.scene, collected)
        self.assertGreater(len(mapping), 0)

        calls: list[tuple[Any, ...]] = []

        class _FakeNM:
            @staticmethod
            def send_gui_update_to_fish(scene_id: int, filter_id: str, key: str,
                                        value: str, enque: bool = False) -> None:
                calls.append((scene_id, filter_id, key, value, enque))

        with patch.object(preview_runtime, "NetworkManager", lambda: _FakeNM):
            thread = PropertyCuesPreviewThread(self.vfilter, mapping, tick_hz=50.0)
            thread.set_timecode(0.0)
            thread.set_cue_index(0)
            thread.set_playing(True)
            thread.start()
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not calls:
                time.sleep(0.02)
            thread.requestInterruption()
            thread.wait(2000)

        self.assertGreater(len(calls), 0, "Expected at least one tick update.")
        emitted_filter_ids = {c[1] for c in calls}
        expected_constant_ids = {entry.split(":", 1)[0] for entry in mapping.values()}
        self.assertTrue(
            emitted_filter_ids.intersection(expected_constant_ids),
            "No tick emitted into any of the preview constant filters.",
        )

    def test_filter_settings_route_to_editor(self) -> None:
        """Verify the filter-settings lookup returns the PropertyCueEditor for the vfilter type."""
        from model.filter import FilterTypeEnumeration
        from view.show_mode.editor.filter_settings_item import check_if_filter_has_special_widget
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        class _FakeFilter:
            filter_type = FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES

        widget = check_if_filter_has_special_widget(_FakeFilter())
        self.assertIsInstance(widget, PropertyCueEditor)

    def test_circle_preset_in_library(self) -> None:
        """Verify the Circle preset ships in the preset library and the vfilter recompiles against it."""
        from model.virtual_filters.property_cues.presets import load_preset_library

        library = load_preset_library()
        self.assertIn("Circle", library,
                      f"Circle preset missing from library: {sorted(library.keys())}")

        # Compiling the vfilter already exercises the Circle reference in cue 2.
        self.vfilter.invalidate_compile_cache()
        self.vfilter._ensure_compiled()

    def test_pan_sweep_writes_pan_and_brightness_channels(self) -> None:
        """Pan Sweep is registered under ``position`` but also drives dimmer.

        The compiler must widen the request group's ``channel_names`` to
        include every raw channel the preset emits that the fixture
        actually supports -- otherwise the brightness stream the preset
        sends is dropped by the solver and the moving head never dims.
        """
        from model.virtual_filters.property_cues.distribution import Distribution
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            PresetPropertyAssignment,
            PropertyAssignments,
            PropertyCue,
            PropertyStep,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        f = PropertyBasedCueFilter(self.scene, "sweep_only")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.POSITION, EnabledCapability.DIMMER},
        )
        f.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=4 * 40, assignments={
                "fixture:MH1": PropertyAssignments(by_property={
                    "position": PresetPropertyAssignment(
                        preset_id="Pan Sweep",
                        hint_values={
                            "angle_a": 0.2, "angle_b": 0.8,
                            "dimmer_a": 1.0, "dimmer_b": 0.3,
                            "seconds": 4.0,
                        },
                        distribution=Distribution(),
                    ),
                }),
            }),
        ]))
        res = f._ensure_compiled()
        native_channels = {name for name, _dt in res.native_model.channels}
        self.assertIn("MH1__pan_value", native_channels)
        self.assertIn("MH1__brightness_raw", native_channels,
                      "Pan Sweep must drive brightness_raw even though its "
                      "applies_for is position; the solver's channel_names "
                      "set widens to include cross-property emissions.")

        # Dump the brightness_raw frames and confirm the preset's dimmer_a/dimmer_b
        # actually landed on the keyframe stream.
        cue = res.native_model.cues[0]
        brightness_idx = next(
            i for i, (name, _dt) in enumerate(cue._channel_definitions)
            if name == "MH1__brightness_raw"
        )
        brightness_values = sorted(
            float(kf._states[brightness_idx]._value) for kf in cue._frames
        )
        self.assertAlmostEqual(0.3, brightness_values[0], places=5)
        self.assertAlmostEqual(1.0, brightness_values[-1], places=5)

    def test_int_key_dicts_survive_json_roundtrip(self) -> None:
        """Regression (L3): gobo slots and colour segments must keep int keys after reload.

        ``json.dumps`` encodes every dict key as a string, so a gobo
        ``{slots: {0: 3, 1: 7}}`` would come back as ``{slots: {"0": 3, "1": 7}}``
        and ``GoboProperty.generate_requests`` would miss every wheel with an
        int lookup. The fix coerces all-decimal-key dicts back to int keys at
        the model boundary.
        """
        import json
        from model.virtual_filters.property_cues.model.property_step import (
            ManualPropertyAssignment,
        )
        # Build a manual gobo assignment with 12 slots (so a lexicographic
        # sort of string keys would also reorder them: "0" < "1" < "10" <
        # "11" < "2" < ...).
        original = ManualPropertyAssignment(
            values={
                "wheel_count": 12,
                "slots": {i: (i * 3) % 7 for i in range(12)},
                "rotations": {i: float(i) / 10.0 for i in range(12)},
            },
        )
        blob = json.loads(json.dumps(original.to_json()))
        reloaded = ManualPropertyAssignment.from_json(blob)
        slots = reloaded.values["slots"]
        rotations = reloaded.values["rotations"]
        self.assertIsInstance(slots, dict)
        for k in slots:
            self.assertIsInstance(k, int, f"Key {k!r} is {type(k).__name__}, expected int")
        for k in rotations:
            self.assertIsInstance(k, int, f"Key {k!r} is {type(k).__name__}, expected int")
        # Round-trip equality: a lookup with an integer key must return the
        # original value, not the default.
        self.assertEqual((5 * 3) % 7, slots[5])
        self.assertAlmostEqual(0.5, rotations[5], places=5)

    def test_unrelated_keyframe_does_not_reshape_fade(self) -> None:
        """Regression (L4): an unrelated channel's keyframe must not turn a fade into a hold.

        Before L4, :func:`_native_builder._state_for` copied the prior
        keyframe's value when the timestamp slot had no hit on this channel.
        A fade 0 → 1 over 2 s on channel A compiled to [0 @ 0 s, 1 @ 2 s].
        Adding a keyframe for another fixture at 1 s introduced the slot
        into the cue's union, and A's state at 1 s became the held prior
        value 0 — turning the fade into "hold 0 until 1 s, then fade to 1
        over 1 s". The fix interpolates in ``_state_for`` using the next
        frame's transition, so A's state at 1 s is the midpoint 0.5.
        """
        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            ManualPropertyAssignment,
            PropertyAssignments,
            PropertyCue,
            PropertyCueFilterModel,
            PropertyStep,
            SelectionEntryKind,
        )
        model = PropertyCueFilterModel()
        model.fixture_selection = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="A"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="B"),
            ],
            enabled_capabilities={EnabledCapability.DIMMER},
        )

        def _dim(brightness: float) -> PropertyAssignments:
            return PropertyAssignments(
                by_property={
                    "dimmer": ManualPropertyAssignment(
                        values={"brightness": brightness, "strobefreq": 0.0},
                    ),
                },
            )
        # Three 1 s steps. A assigns only at steps 0 and 2 (slots 0, 80), so
        # A's keyframes bracket the cue 0s..2s with no hit at slot 40. B
        # assigns at steps 0 and 1 (slots 0, 40), which adds slot 40 to the
        # cue-wide union. The L4 fix must interpolate A at slot 40 instead
        # of holding A's prior value.
        model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40, assignments={
                "fixture:A": _dim(0.0),
                "fixture:B": _dim(0.1),
            }),
            PropertyStep(name="s1", duration_40hz=40, assignments={
                "fixture:B": _dim(0.9),
            }),
            PropertyStep(name="s2", duration_40hz=40, assignments={
                "fixture:A": _dim(1.0),
            }),
        ]))
        res = compile_property_model(model, cue_filter_id="pcf_l4", scene=self.scene)
        cue = res.native_model.cues[0]
        a_idx = next(
            i for i, (name, _dt) in enumerate(cue._channel_definitions)
            if name == "A__brightness_raw"
        )
        # At t=1 s (slot 40, between A's 0@0 s and 1@2 s), A must be ~0.5,
        # not the held 0.0 — because B contributes a slot at 40 and A's
        # state must be the interpolation of A's bracket at that slot.
        # Find the frame at slot 40 (t=1 s).
        slot40 = [kf for kf in cue._frames if round(kf.timestamp, 3) == 1.0]
        self.assertTrue(slot40, "Expected a combined keyframe at t=1.0 s")
        a_value_at_1s = float(slot40[0]._states[a_idx]._value)
        self.assertAlmostEqual(
            0.5, a_value_at_1s, places=3,
            msg=f"A's interpolated value at t=1 s should be 0.5, got {a_value_at_1s}",
        )

    def test_consolidation_preserves_divergent_strobe_wiring(self) -> None:
        """Regression (L1): same brightness + different strobe freq must not merge.

        Before L1, the post-process chain cache was keyed on
        ``(canonical_prefix, capability)``. When MH1's brightness consolidated
        onto MH2 (identical stream) but their strobe-freq streams diverged,
        the strategy for MH2 reused MH1's chain — so MH2's ``brightness``
        port silently pointed at MH1's strobe generator which drew MH1's
        frequency, and MH2's own strobefreq was ignored. The fix keys the
        cache on the sorted tuple of canonical input sources so divergent
        wiring forces a new chain.
        """
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            ManualPropertyAssignment,
            PropertyAssignments,
            PropertyCue,
            PropertyStep,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        def _dimmer(brightness: float, strobefreq: float) -> PropertyAssignments:
            return PropertyAssignments(
                by_property={
                    "dimmer": ManualPropertyAssignment(
                        values={"brightness": brightness, "strobefreq": strobefreq},
                    ),
                },
            )

        vfilter = PropertyBasedCueFilter(self.scene, "pcf_l1")
        vfilter.property_model.fixture_selection = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH2"),
            ],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        vfilter.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40, assignments={
                "fixture:MH1": _dimmer(0.5, 2.0),  # 2 Hz strobe
                "fixture:MH2": _dimmer(0.5, 5.0),  # 5 Hz strobe — SAME brightness,
                                                   # different frequency
            }),
        ]))
        res = vfilter._ensure_compiled()
        strobes = tuple(
            f for f in res.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
        )
        # Must have TWO strobe generators — one per fixture — because strobefreq
        # didn't consolidate even though brightness_raw did.
        self.assertEqual(
            2, len(strobes),
            f"Expected 2 strobe generators (divergent strobefreq), got {len(strobes)}: "
            f"{[s.filter_id for s in strobes]}",
        )
        # Each strobe generator's frequency input must come from the right
        # fixture's own strobefreq (not consolidated to the sibling).
        strobe_by_prefix = {}
        for s in strobes:
            # Strobe filter id matches "{cue_fid}__{prefix}__dimmer_strobe";
            # the prefix lives between the cue_fid and the dimmer_strobe
            # suffix. Here cue_fid == "pcf_l1" (no "__") so we can strip it.
            suffix_tail = "__dimmer_strobe"
            self.assertTrue(s.filter_id.endswith(suffix_tail))
            without_suffix = s.filter_id[:-len(suffix_tail)]
            # The remaining string is "{cue_fid}__{prefix}"; prefix is after
            # the first "__".
            parts = without_suffix.split("__", 1)
            if len(parts) == 2:
                strobe_by_prefix[parts[1]] = s
        mh1_strobe = strobe_by_prefix.get("MH1")
        mh2_strobe = strobe_by_prefix.get("MH2")
        self.assertIsNotNone(mh1_strobe,
                             f"Could not locate MH1 strobe among {list(strobe_by_prefix)}")
        self.assertIsNotNone(mh2_strobe,
                             f"Could not locate MH2 strobe among {list(strobe_by_prefix)}")
        # MH2's strobe must read from a chain whose freq ultimately resolves
        # to MH2__strobefreq, not MH1__strobefreq. The freq input goes
        # through the float-to-8bit adapter; follow the chain.
        mh2_freq_link = mh2_strobe.channel_links["frequency"]
        self.assertIn("MH2", mh2_freq_link,
                      f"MH2's strobe reads from the wrong fixture's chain: {mh2_freq_link}")
        self.assertNotIn("MH1__strobefreq", mh2_freq_link,
                         f"MH2's strobe pulled MH1's strobefreq: {mh2_freq_link}")

    def test_cue_length_matches_sum_of_step_durations(self) -> None:
        """Regression (L5): the last step's duration must reach the compiled cue.

        Before L5 each step emitted a keyframe only at its start, so a two-
        step cue 1 s + 10 s compiled to a cue ending at 1.0 s (fish
        treats the last keyframe timestamp as the cue's end). After L5 the
        compiler synthesises a closing keyframe at the sum of all step
        durations.
        """
        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            ManualPropertyAssignment,
            PropertyAssignments,
            PropertyCue,
            PropertyCueFilterModel,
            PropertyStep,
            SelectionEntryKind,
        )
        model = PropertyCueFilterModel()
        model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="A")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )

        def _dim(brightness: float) -> PropertyAssignments:
            return PropertyAssignments(
                by_property={
                    "dimmer": ManualPropertyAssignment(
                        values={"brightness": brightness, "strobefreq": 0.0},
                    ),
                },
            )
        model.cues.append(PropertyCue(name="C1", steps=[
            # 1 s + 10 s = 11 s.
            PropertyStep(name="s0", duration_40hz=40,  assignments={"fixture:A": _dim(0.3)}),
            PropertyStep(name="s1", duration_40hz=400, assignments={"fixture:A": _dim(0.8)}),
        ]))
        res = compile_property_model(model, cue_filter_id="pcf_l5", scene=self.scene)
        cue = res.native_model.cues[0]
        last_timestamp = max(kf.timestamp for kf in cue._frames)
        self.assertAlmostEqual(
            11.0, last_timestamp, places=3,
            msg=f"Cue must end at 11.0 s (1 + 10), got {last_timestamp}",
        )
        a_idx = next(
            i for i, (name, _dt) in enumerate(cue._channel_definitions)
            if name == "A__brightness_raw"
        )
        last_frame = max(cue._frames, key=lambda kf: kf.timestamp)
        self.assertAlmostEqual(0.8, float(last_frame._states[a_idx]._value), places=3,
                               msg="Closing keyframe must repeat the last authored value")

    def test_fixture_override_holds_across_step_duration(self) -> None:
        """Regression (L6): a fixture-level override must hold for the whole step.

        Before L6, a step-level assignment produced a separate RequestGroup
        for every fixture it covered, and the solver reconciled per-slot.
        If the step-level emission landed on a slot the fixture-level
        override did not touch (e.g. because of a distribution delay), the
        step-level value "leaked through" at that slot, overwriting the
        override mid-step. The fix is to resolve precedence per
        ``(fixture, property, step)`` in :func:`_collect_cue` and only
        emit the winning assignment's requests.
        """
        from model.filter_data.transfer_function import TransferFunction
        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.distribution import (
            Distribution,
            DistributionMethod,
        )
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            ManualPropertyAssignment,
            PropertyAssignments,
            PropertyCue,
            PropertyCueFilterModel,
            PropertyStep,
            SelectionEntryKind,
        )
        model = PropertyCueFilterModel()
        model.fixture_selection = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="A"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="B"),
            ],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        # Step-level assignment (brightness=1.0) with a linear per-child delay:
        # fixture A @ t=0, fixture B @ t=0.5s. Fixture-level override on B
        # (brightness=0.25) which should hold for the entire step on B.
        step_level = PropertyAssignments(
            by_property={
                "dimmer": ManualPropertyAssignment(
                    values={"brightness": 1.0, "strobefreq": 0.0},
                    distribution=Distribution(
                        method=DistributionMethod.PHASE_LINEAR,
                        phase_offset=0.5, amplitude=1.0,
                    ),
                ),
            },
        )
        override = PropertyAssignments(
            by_property={
                "dimmer": ManualPropertyAssignment(
                    values={"brightness": 0.25, "strobefreq": 0.0},
                ),
            },
        )
        model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=80, assignments={
                "": step_level,
                "fixture:B": override,
            }),
        ]))
        res = compile_property_model(model, cue_filter_id="pcf_l6", scene=self.scene)
        cue = res.native_model.cues[0]
        b_raw_idx = next(
            i for i, (name, _dt) in enumerate(cue._channel_definitions)
            if name == "B__brightness_raw"
        )
        # Collect every brightness_raw value emitted for fixture B across the
        # step. None of them should be the step-level value 1.0 — the override
        # 0.25 must dominate throughout.
        b_raw_values = {round(float(kf._states[b_raw_idx]._value), 5) for kf in cue._frames}
        self.assertIn(0.25, b_raw_values)
        self.assertNotIn(1.0, b_raw_values,
                         f"Step-level 1.0 leaked into B's stream: {b_raw_values}")
        # Suppress linter warning for unused import — present so the test runs
        # even if the transfer function constants aren't referenced below.
        _ = TransferFunction


if __name__ == "__main__":
    unittest.main()
