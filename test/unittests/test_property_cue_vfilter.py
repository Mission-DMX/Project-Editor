"""Unit tests for the PropertyBasedCueFilter vfilter shell (WP9)."""

from __future__ import annotations

import gc
import importlib.util
import sys
import unittest
from logging import getLogger

from model.filter import DataType, FilterTypeEnumeration
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

logger = getLogger(__name__)

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None

_qapp = None


def setUpModule() -> None:  # noqa: N802 — unittest hook naming
    """Create a ``QApplication`` so ``Scene`` can be constructed in tests."""
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 — unittest hook naming
    gc.enable()


def _make_scene():
    from model import BoardConfiguration, Scene

    show = BoardConfiguration()
    scene = Scene(0, "Test property-cue vfilter scene", show)
    show._add_scene(scene)
    return scene


def _manual_dimmer(brightness: float) -> PropertyAssignments:
    return PropertyAssignments(
        by_property={
            "dimmer": ManualPropertyAssignment(
                values={"brightness": brightness, "strobefreq": 0.0},
            ),
        },
    )


@unittest.skipUnless(_HAS_PYSIDE, "Scene constructor requires PySide6")
class PropertyBasedCueVFilterTests(unittest.TestCase):

    def test_default_empty_io(self) -> None:
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_default")
        self.assertEqual(DataType.DT_DOUBLE, f.in_data_types["time"])
        self.assertEqual(DataType.DT_DOUBLE, f.in_data_types["time_scale"])
        self.assertEqual("1.0", f.default_values["time_scale"])
        self.assertEqual({}, f.out_data_types)
        self.assertIn("cues-prop-data", f.filter_configurations)

    def test_roundtrip_configuration(self) -> None:
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_rt")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        cue = PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40,
                         assignments={"fixture:MH1": _manual_dimmer(0.5)}),
        ])
        f.property_model.cues.append(cue)
        f.serialize()
        self.assertNotEqual("", f.filter_configurations["cues-prop-data"])

        # Re-create a fresh filter and deserialize into it.
        g = PropertyBasedCueFilter(scene, "pcf_rt_reload")
        g.filter_configurations["cues-prop-data"] = f.filter_configurations["cues-prop-data"]
        g.deserialize()
        self.assertEqual(1, len(g.property_model.cues))
        reloaded_step = g.property_model.cues[0].steps[0]
        self.assertEqual("s0", reloaded_step.name)
        assign = reloaded_step.assignments["fixture:MH1"].by_property["dimmer"]
        self.assertIsInstance(assign, ManualPropertyAssignment)
        self.assertEqual(0.5, assign.values["brightness"])

    def test_resolve_passthrough(self) -> None:
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_pt")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        f.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40,
                         assignments={"fixture:MH1": _manual_dimmer(0.5)}),
        ]))
        resolved = f.resolve_output_port_id("MH1__brightness")
        self.assertIsNotNone(resolved)
        self.assertEqual(f"{f.filter_id}:MH1__brightness", resolved)
        # Dimmer capability is not in the postprocess strategy table, so an
        # explicit capability port name should also resolve via passthrough.
        resolved_cap = f.resolve_output_port_id("MH1__dimmer")
        self.assertIsNotNone(resolved_cap)
        self.assertEqual(f"{f.filter_id}:MH1__dimmer", resolved_cap)

    def test_resolve_consolidated(self) -> None:
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_cons")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH2"),
            ],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        cue = PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40, assignments={
                "fixture:MH1": _manual_dimmer(0.5),
                "fixture:MH2": _manual_dimmer(0.5),
            }),
        ])
        f.property_model.cues.append(cue)
        resolved_mh1 = f.resolve_output_port_id("MH1__brightness")
        resolved_mh2 = f.resolve_output_port_id("MH2__brightness")
        self.assertIsNotNone(resolved_mh1)
        self.assertIsNotNone(resolved_mh2)
        self.assertEqual(resolved_mh1, resolved_mh2)
        # Canonical name picks the alphabetically-earliest channel (MH1).
        self.assertEqual(f"{f.filter_id}:MH1__brightness", resolved_mh1)

    def test_preview_mode_builds_constant_mapping(self) -> None:
        # WP12 replaced the WP9 stub: preview instantiation now delegates to
        # :func:`build_preview_filters`, so the vfilter must expose a channel
        # mapping instead of raising ``NotImplementedError``.
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_prev")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        f.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40,
                         assignments={"fixture:MH1": _manual_dimmer(0.5)}),
        ]))
        f.in_preview_mode = True
        instantiated: list = []
        f.instantiate_filters(instantiated)
        self.assertGreater(len(instantiated), 0)
        self.assertNotEqual({}, f._channel_mapping)

    def test_factory_registration(self) -> None:
        from model.virtual_filters.vfilter_factory import (
            _construct_virtual_filter_instance_legacy,
        )

        scene = _make_scene()
        instance = _construct_virtual_filter_instance_legacy(
            scene, int(FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES), "test_id",
        )
        self.assertIsInstance(instance, PropertyBasedCueFilter)


if __name__ == "__main__":
    unittest.main()
