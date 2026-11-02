"""Unit tests for the property-based cue vfilter live-preview runtime (WP12)."""

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
    """Spin a QApplication so Scene / QThread construction works in tests."""
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
    scene = Scene(0, "Test preview-runtime scene", show)
    show._add_scene(scene)
    return scene


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


def _manual_colour(hue: float, saturation: float, intensity: float):
    from model.color_hsi import ColorHSI
    from model.virtual_filters.property_cues.model import (
        ManualPropertyAssignment,
        PropertyAssignments,
    )

    return PropertyAssignments(
        by_property={
            "colour": ManualPropertyAssignment(
                values={"color": ColorHSI(hue, saturation, intensity)},
            ),
        },
    )


def _make_vfilter_two_dimmer_fixtures(scene):
    from model.virtual_filters.property_cues.model import (
        EnabledCapability,
        FixtureSelection,
        FixtureSelectionEntry,
        PropertyCue,
        PropertyStep,
        SelectionEntryKind,
    )
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

    f = PropertyBasedCueFilter(scene, "pcf_preview")
    f.property_model.fixture_selection = FixtureSelection(
        entries=[
            FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1"),
            FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH2"),
        ],
        enabled_capabilities={EnabledCapability.DIMMER},
    )
    f.property_model.cues.append(
        PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=80, assignments={
                "fixture:MH1": _manual_dimmer(0.25),
                "fixture:MH2": _manual_dimmer(0.75),
            }),
        ]),
    )
    return f


def _make_vfilter_single_colour(scene):
    from model.virtual_filters.property_cues.model import (
        EnabledCapability,
        FixtureSelection,
        FixtureSelectionEntry,
        PropertyCue,
        PropertyStep,
        SelectionEntryKind,
    )
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

    f = PropertyBasedCueFilter(scene, "pcf_colour")
    f.property_model.fixture_selection = FixtureSelection(
        entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
        enabled_capabilities={EnabledCapability.COLOUR},
    )
    f.property_model.cues.append(
        PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=80, assignments={
                "fixture:MH1": _manual_colour(120.0, 1.0, 0.5),
            }),
            PropertyStep(name="s1", duration_40hz=80, assignments={
                "fixture:MH1": _manual_colour(240.0, 1.0, 0.5),
            }),
        ]),
    )
    return f


@unittest.skipUnless(_HAS_PYSIDE, "Preview runtime requires PySide6")
class BuildPreviewFiltersTests(unittest.TestCase):

    def test_build_preview_filters_creates_constants(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.property_cues.preview_runtime import (
            build_preview_filters,
        )

        scene = _make_scene()
        vfilter = _make_vfilter_two_dimmer_fixtures(scene)
        collected: list = []
        mapping = build_preview_filters(vfilter, scene, collected)

        self.assertGreaterEqual(len(collected), 2)
        constant_types = {
            FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
            FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
            FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
        }
        for f in collected:
            self.assertIn(int(f.filter_type), {int(t) for t in constant_types})
        self.assertGreater(len(mapping), 0)
        for mapped in mapping.values():
            self.assertTrue(mapped.endswith(":value"))


@unittest.skipUnless(_HAS_PYSIDE, "Preview runtime requires PySide6")
class PreviewThreadLifecycleTests(unittest.TestCase):

    def test_thread_shutdown_clean(self) -> None:
        from model.virtual_filters.property_cues.preview_runtime import (
            PropertyCuesPreviewThread,
            build_preview_filters,
        )

        scene = _make_scene()
        vfilter = _make_vfilter_two_dimmer_fixtures(scene)
        collected: list = []
        mapping = build_preview_filters(vfilter, scene, collected)

        thread = PropertyCuesPreviewThread(vfilter, mapping, tick_hz=50.0)
        thread.start()
        thread.requestInterruption()
        self.assertTrue(thread.wait(2000),
                        "Preview thread did not exit within the timeout.")
        self.assertFalse(thread.isRunning())


@unittest.skipUnless(_HAS_PYSIDE, "Preview runtime requires PySide6")
class PreviewThreadEmitTests(unittest.TestCase):

    def test_tick_sends_updates(self) -> None:
        from model.virtual_filters.property_cues import preview_runtime
        from model.virtual_filters.property_cues.preview_runtime import (
            PropertyCuesPreviewThread,
            build_preview_filters,
        )

        scene = _make_scene()
        vfilter = _make_vfilter_two_dimmer_fixtures(scene)
        collected: list = []
        mapping = build_preview_filters(vfilter, scene, collected)
        self.assertGreater(len(mapping), 0)

        calls: list[tuple[Any, ...]] = []

        class _FakeNM:
            @staticmethod
            def send_gui_update_to_fish(scene_id: int, filter_id: str, key: str,
                                        value: str, enque: bool = False) -> None:
                calls.append((scene_id, filter_id, key, value, enque))

        with patch.object(preview_runtime, "NetworkManager", lambda: _FakeNM):
            thread = PropertyCuesPreviewThread(vfilter, mapping, tick_hz=50.0)
            thread.set_timecode(0.0)
            thread.set_cue_index(0)
            thread.set_playing(True)
            thread.start()
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not calls:
                time.sleep(0.02)
            thread.requestInterruption()
            thread.wait(2000)

        self.assertGreater(len(calls), 0, "Expected at least one GUI update tick.")
        constant_ids = {entry.split(":", 1)[0] for entry in mapping.values()}
        emitted_ids = {call[1] for call in calls}
        self.assertTrue(constant_ids.intersection(emitted_ids))
        for call in calls:
            self.assertEqual("value", call[2])
            self.assertEqual(scene.scene_id, call[0])

    def test_color_channel_format(self) -> None:
        from model.color_hsi import ColorHSI
        from model.virtual_filters.property_cues import preview_runtime
        from model.virtual_filters.property_cues.preview_runtime import (
            PropertyCuesPreviewThread,
            build_preview_filters,
        )

        scene = _make_scene()
        vfilter = _make_vfilter_single_colour(scene)
        collected: list = []
        mapping = build_preview_filters(vfilter, scene, collected)
        self.assertGreater(len(mapping), 0)

        calls: list[tuple[Any, ...]] = []

        class _FakeNM:
            @staticmethod
            def send_gui_update_to_fish(scene_id: int, filter_id: str, key: str,
                                        value: str, enque: bool = False) -> None:
                calls.append((scene_id, filter_id, key, value, enque))

        # Figure out the half-way timecode for the compiled cue so we're inside
        # a segment (not clamping to a boundary).
        cue = vfilter._last_compile.native_model.cues[0]
        timestamps = sorted({kf.timestamp for kf in cue._frames})
        self.assertGreaterEqual(len(timestamps), 2)
        mid_time = (timestamps[0] + timestamps[-1]) / 2.0

        with patch.object(preview_runtime, "NetworkManager", lambda: _FakeNM):
            thread = PropertyCuesPreviewThread(vfilter, mapping, tick_hz=50.0)
            thread.set_timecode(mid_time)
            thread.set_cue_index(0)
            thread.set_playing(True)
            thread.start()
            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline and not calls:
                time.sleep(0.02)
            thread.requestInterruption()
            thread.wait(2000)

        self.assertGreater(len(calls), 0, "Expected at least one GUI update tick.")
        # Any colour-formatted value is "hue,sat,int" — three comma-separated floats.
        colour_payloads = [c[3] for c in calls if c[3].count(",") == 2]
        self.assertGreater(len(colour_payloads), 0,
                           "Expected a ColorHSI-formatted update payload.")
        parsed = ColorHSI.from_filter_str(colour_payloads[0])
        # Hue of a sanely interpolated green/blue segment stays finite and in-range.
        self.assertTrue(0.0 <= parsed.hue < 360.0)


if __name__ == "__main__":
    unittest.main()
