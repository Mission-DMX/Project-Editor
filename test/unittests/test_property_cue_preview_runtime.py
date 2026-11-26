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
    """Re-enable garbage collection after the module-level tests have finished."""
    gc.enable()


def _make_scene():
    """Return a fresh Scene bound to a BoardConfiguration for use in preview-runtime tests."""
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
            "color": ManualPropertyAssignment(
                values={"colors": {0: ColorHSI(hue, saturation, intensity)}},
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
        enabled_capabilities={EnabledCapability.COLOR},
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
    """Verify build_preview_filters emits the expected constant/postprocess filter graph."""

    def test_build_preview_filters_creates_constants(self) -> None:
        """Verify preview build emits PREVIEW_CONST filters for every raw canonical channel."""
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.property_cues.preview_runtime import (
            build_preview_filters,
        )

        scene = _make_scene()
        vfilter = _make_vfilter_two_dimmer_fixtures(scene)
        collected: list = []
        mapping = build_preview_filters(vfilter, scene, collected)

        self.assertGreaterEqual(len(collected), 2)
        # Preview emits two kinds of filters: PREVIEW_CONSTs (one per
        # canonical raw channel feeding the postprocess chain) and the
        # cloned postprocess chain itself (strobe-generator, pan/tilt
        # sin/cos/switch/range). The constants seed the chain with the
        # preview thread's per-tick values; the chain reproduces the
        # production synthesis so downstream adapters still read
        # ``X__pan`` etc. from the same ``_range:value`` port fish will
        # see in production.
        constant_types = {
            FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
            FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
            FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
        }
        constants = [f for f in collected if int(f.filter_type) in {int(t) for t in constant_types}]
        self.assertGreater(len(constants), 0, "No PREVIEW_CONST filters were emitted.")
        for f in constants:
            self.assertIn(
                "__PREVIEW_CONST__", f.filter_id,
                f"Unexpected constant filter id {f.filter_id!r}",
            )
        self.assertGreater(len(mapping), 0)
        for mapped in mapping.values():
            self.assertTrue(mapped.endswith(":value"))

    def test_8bit_spec_gets_8bit_preview_const(self) -> None:
        """Regression: DT_8_BIT specs must produce FILTER_CONSTANT_8BIT.

        Fish rejected the preview scene with
        ``channel mapping does not contain channel 'select' of type 'uint8_t'``
        because every PREVIEW_CONST was 16-bit regardless of the spec's
        actual width; the cloned pan/tilt ``switch`` filter's ``select``
        input is uint8 so the type mismatch broke scheduling.
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
        from model.virtual_filters.property_cues.preview_runtime import (
            build_preview_filters,
        )
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        scene = _make_scene()
        vfilter = PropertyBasedCueFilter(scene, "pcf_8bit")
        vfilter.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.POSITION},
        )
        vfilter.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=80, assignments={
                "fixture:MH1": PropertyAssignments(by_property={
                    "position": ManualPropertyAssignment(values={
                        "pan_value": 0.5, "pan_curvesel": 1,
                        "tilt_value": 0.5, "tilt_curvesel": 2,
                    }),
                }),
            }),
        ]))

        collected: list = []
        build_preview_filters(vfilter, scene, collected)

        curvesel_consts = [
            f for f in collected
            if "curvesel" in f.filter_id and "__PREVIEW_CONST__" in f.filter_id
        ]
        self.assertGreater(len(curvesel_consts), 0,
                           "No PREVIEW_CONST filters for curvesel channels were emitted.")
        for f in curvesel_consts:
            self.assertEqual(
                int(FilterTypeEnumeration.FILTER_CONSTANT_8BIT),
                int(f.filter_type),
                f"curvesel PREVIEW_CONST {f.filter_id!r} must be 8-bit so it "
                f"matches the switch 'select' input type on fish's side.",
            )

    def test_synthesized_pan_resolves_to_a_live_filter(self) -> None:
        """Regression: ``X__pan`` must map to a filter that actually exists.

        Fish rejected the preview scene with
        ``The requested scene does not contain the requested filter
        'Property Cues.0__PREVIEW_CONST__..._pan_value'`` because the earlier
        implementation only populated the mapping for the raw channel names
        in ``channel_specs`` (``pan_value``, ``pan_curvesel`` …) and left the
        synthesized port ``X__pan`` out. ``resolve_output_port_id`` then
        returned ``None`` for every adapter's ``Property Cues.0:X__pan``
        channel_link, and the serializer kept the unresolved string.

        The fix emits the postprocess chain (sin/cos/switch/range) into the
        preview filter graph and keys the mapping off ``external_ports`` so
        both raw and synthesized virtual ports resolve. Every value in the
        mapping must therefore reference a filter id that appears in the
        emitted filter list (or one of the compile's ``__CONST__`` filters
        already present in ``postprocess_filters``).
        """
        from model.virtual_filters.property_cues.model import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            PropertyCue,
            PropertyStep,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.preview_runtime import (
            build_preview_filters,
        )
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        scene = _make_scene()
        vfilter = PropertyBasedCueFilter(scene, "pcf_preview_pos")
        vfilter.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.POSITION},
        )
        # Give the fixture a live position stream so the strategy chain stays
        # in the compile (the default-fold path would otherwise collapse it
        # to a single constant).
        from model.virtual_filters.property_cues.model import (
            ManualPropertyAssignment,
            PropertyAssignments,
        )
        vfilter.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=80, assignments={
                "fixture:MH1": PropertyAssignments(by_property={
                    "position": ManualPropertyAssignment(values={
                        "pan_value": 0.3, "pan_curvesel": 0,
                        "tilt_value": 0.7, "tilt_curvesel": 0,
                    }),
                }),
            }),
        ]))

        collected: list = []
        mapping = build_preview_filters(vfilter, scene, collected)

        # Every virtual port the serializer will query must have a
        # downstream-visible target. The compile emits some ``__CONST__``
        # filters (defaulted canonicals) as part of ``postprocess_filters``;
        # we accept those as well as anything we emitted ourselves.
        emitted_filter_ids = {f.filter_id for f in collected}
        emitted_filter_ids.update(
            f.filter_id for f in vfilter._last_compile.postprocess_filters
        )
        for virtual_port, mapped in mapping.items():
            filter_id = mapped.split(":", 1)[0]
            self.assertIn(
                filter_id, emitted_filter_ids,
                f"mapping['{virtual_port}'] = '{mapped}' points at a filter the "
                f"preview did not emit; downstream adapter channel_links would "
                f"dangle. Emitted: {sorted(emitted_filter_ids)}",
            )
        # The synthesized ``X__pan`` and ``X__tilt`` ports specifically must
        # be in the mapping -- those are the ones the fish log complained
        # about.
        self.assertIn("MH1__pan", mapping)
        self.assertIn("MH1__tilt", mapping)


@unittest.skipUnless(_HAS_PYSIDE, "Preview runtime requires PySide6")
class PreviewThreadLifecycleTests(unittest.TestCase):
    """Verify the preview thread starts and shuts down cleanly."""

    def test_thread_shutdown_clean(self) -> None:
        """Verify requesting interruption causes the preview thread to exit within the timeout."""
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
    """Verify the preview thread emits per-tick GUI updates in the expected format."""

    def test_tick_sends_updates(self) -> None:
        """Verify running the preview thread emits GUI updates into the preview constant filters."""
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
        """Verify colour-channel preview updates are sent as 'hue,sat,int' payloads."""
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
