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
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 - unittest hook
    gc.enable()


def _make_scene():
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
            "fixture:MH1": _preset_position("Circle", {"speed": 40.0, "size": 1.0}),
            "fixture:MH2": _manual_position(0.5, 0.75),
        }),
    ])
    vfilter.property_model.cues.append(cue1)
    vfilter.property_model.cues.append(cue2)
    return vfilter


@unittest.skipUnless(_HAS_PYSIDE, "Property cue vfilter requires PySide6")
class PropertyCueEndToEndTests(unittest.TestCase):

    def setUp(self) -> None:
        self.show, self.scene = _make_scene()
        self.vfilter = _build_populated_filter(self.scene)

    def test_full_pipeline_dimmer_position_preset(self) -> None:
        from model.filter import FilterTypeEnumeration

        res = self.vfilter._ensure_compiled()
        native_channels = {name for name, _dt in res.native_model.channels}
        for ch in ("MH1__brightness", "MH2__brightness",
                   "MH1__pan_value", "MH2__pan_value",
                   "MH1__pan_curvesel", "MH2__pan_curvesel",
                   "MH1__tilt_value", "MH2__tilt_value",
                   "MH1__tilt_curvesel", "MH2__tilt_curvesel"):
            self.assertIn(ch, native_channels, f"missing native channel: {ch}")

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

    def test_serialize_deserialize_roundtrip(self) -> None:
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
        vfilter._ensure_compiled()
        a = vfilter.resolve_output_port_id("MH1__brightness")
        b = vfilter.resolve_output_port_id("MH2__brightness")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertEqual(a, b)

    def test_preview_thread_tick_for_cue(self) -> None:
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
        from model.virtual_filters.property_cues.presets import load_preset_library

        library = load_preset_library()
        self.assertIn("Circle", library,
                      f"Circle preset missing from library: {sorted(library.keys())}")

        # Compiling the vfilter already exercises the Circle reference in cue 2.
        self.vfilter.invalidate_compile_cache()
        self.vfilter._ensure_compiled()


if __name__ == "__main__":
    unittest.main()
