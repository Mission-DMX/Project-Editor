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

    def test_rebuild_io_populates_outputs_from_model(self) -> None:
        """After the model carries a configured fixture + assignment, the
        vfilter's ``out_data_types`` must reflect the compiled channels so the
        pyqtgraph node can grow terminals for them."""
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_outputs")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        f.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40,
                         assignments={"fixture:MH1": _manual_dimmer(0.5)}),
        ]))
        self.assertEqual({}, f.out_data_types)
        f._rebuild_io()
        self.assertIn("MH1__brightness", f.out_data_types)

    def test_output_names_use_fixture_stage_name_when_board_knows_it(self) -> None:
        """When a fixture's UUID resolves to a stage name on the board, output
        channels should carry that readable name instead of the raw UUID."""
        from unittest.mock import MagicMock, PropertyMock
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_names")
        fixture_uuid = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"
        mock_fixture = MagicMock()
        mock_fixture.uuid = fixture_uuid
        mock_fixture.name_on_stage = "Hero Spot 1"
        # BoardConfiguration.fixtures has no public setter, so patch via descriptor.
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[mock_fixture])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=fixture_uuid)],
                enabled_capabilities={EnabledCapability.DIMMER},
            )
            f.property_model.cues.append(PropertyCue(name="C1", steps=[
                PropertyStep(name="s0", duration_40hz=40,
                             assignments={f"fixture:{fixture_uuid}": _manual_dimmer(0.5)}),
            ]))
            f._rebuild_io()
            self.assertIn("Hero_Spot_1__brightness", f.out_data_types)
            self.assertNotIn("30ed4259_e513_4c9e_87ef_bf822a46b2c5__brightness", f.out_data_types)
        finally:
            # Restore so later tests see the real descriptor.
            del type(scene.board_configuration).fixtures

    def test_enabled_capability_exposes_channels_even_without_assignment(self) -> None:
        """Enabling POSITION on a fixture must create pan/tilt output channels
        even when the user hasn't yet dialed in a value."""
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_defaults")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.POSITION},
        )
        # No cue, no assignment -- just the enabled capabilities.
        f._rebuild_io()
        for channel in (
            "MH1__brightness", "MH1__strobefreq", "MH1__duty_cycle",
            "MH1__pan_value", "MH1__pan_curvesel",
            "MH1__tilt_value", "MH1__tilt_curvesel",
        ):
            self.assertIn(channel, f.out_data_types, f"missing {channel}")

    def test_capability_lookup_restricts_to_supported_capabilities(self) -> None:
        """A fixture without a gobo wheel must not expose gobo channels even
        when the user enabled GOBO on the global selection (wash fixtures)."""
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import WheelSlotType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_wash")
        wash_uuid = "aaaabbbb-cccc-dddd-eeee-ffff00001111"
        colour_slot = MagicMock(); colour_slot.type = WheelSlotType.COLOR
        colour_wheel = MagicMock(); colour_wheel.slots = [colour_slot]
        wash = MagicMock()
        wash.uuid = wash_uuid
        wash.name_on_stage = "Hero Wash"
        wash.fixture_channels = ()
        wash._fixture = MagicMock()
        wash._fixture.wheels = {"Colour Wheel": colour_wheel}
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[wash])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=wash_uuid)],
                enabled_capabilities={EnabledCapability.COLOUR, EnabledCapability.GOBO},
            )
            f._rebuild_io()
            self.assertIn("Hero_Wash__color", f.out_data_types)
            self.assertNotIn("Hero_Wash__goboslot_0", f.out_data_types)
            self.assertNotIn("Hero_Wash__goborotation_0", f.out_data_types)
        finally:
            del type(scene.board_configuration).fixtures

    def test_gobo_wheel_count_lookup_feeds_multiple_wheel_pairs(self) -> None:
        """A Hero-Spot-style fixture with two gobo wheels must expose channels
        for both wheels, not just wheel 0."""
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import WheelSlotType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_spot")
        spot_uuid = "11112222-3333-4444-5555-666677778888"
        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        wheel_a = MagicMock(); wheel_a.slots = [gobo_slot]
        wheel_b = MagicMock(); wheel_b.slots = [gobo_slot]
        spot = MagicMock()
        spot.uuid = spot_uuid
        spot.name_on_stage = "Hero Spot"
        spot.fixture_channels = ()
        spot._fixture = MagicMock()
        spot._fixture.wheels = {"Gobo Wheel": wheel_a, "Rotatable Gobo Wheel": wheel_b}
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[spot])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=spot_uuid)],
                enabled_capabilities={EnabledCapability.GOBO},
            )
            f._rebuild_io()
            for channel in (
                "Hero_Spot__goboslot_0", "Hero_Spot__goborotation_0",
                "Hero_Spot__goboslot_1", "Hero_Spot__goborotation_1",
            ):
                self.assertIn(channel, f.out_data_types, f"missing {channel}")
        finally:
            del type(scene.board_configuration).fixtures

    def test_out_data_types_ordered_by_fixture_then_property(self) -> None:
        """Output terminals must be grouped alphabetically by fixture, then by
        property group (dimmer, position, colour, gobo, beam, focus, frost),
        then within property by the natural channel order so a human can scan
        them top-to-bottom."""
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType, WheelSlotType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_ordering")

        def _ofl_cap(cap_type):
            cap = MagicMock(); cap.type = cap_type
            return cap

        def _channel(name: str, caps: list):
            template = MagicMock(); template.get_capabilities.return_value = caps
            ch = MagicMock(); ch.name = name; ch.channel_template = template
            return ch

        alpha_uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        bravo_uuid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        wheel = MagicMock(); wheel.slots = [gobo_slot]

        alpha = MagicMock(); alpha.uuid = alpha_uuid; alpha.name_on_stage = "Alpha"
        alpha.fixture_channels = (
            _channel("Pan", [_ofl_cap(CapabilityType.PAN)]),
            _channel("Tilt", [_ofl_cap(CapabilityType.TILT)]),
            _channel("Intensity", [_ofl_cap(CapabilityType.INTENSITY)]),
            _channel("Zoom", [_ofl_cap(CapabilityType.ZOOM)]),
            _channel("Focus", [_ofl_cap(CapabilityType.FOCUS)]),
        )
        alpha._fixture = MagicMock(); alpha._fixture.wheels = {"Gobo Wheel": wheel}

        bravo = MagicMock(); bravo.uuid = bravo_uuid; bravo.name_on_stage = "Bravo"
        bravo.fixture_channels = (
            _channel("Pan", [_ofl_cap(CapabilityType.PAN)]),
            _channel("Tilt", [_ofl_cap(CapabilityType.TILT)]),
            _channel("Intensity", [_ofl_cap(CapabilityType.INTENSITY)]),
            _channel("R", [_ofl_cap(CapabilityType.COLOR_INTENSITY)]),
        )
        bravo._fixture = MagicMock(); bravo._fixture.wheels = {}

        type(scene.board_configuration).fixtures = PropertyMock(return_value=[alpha, bravo])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[
                    # Deliberately out-of-order to prove the sort kicks in.
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=bravo_uuid),
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=alpha_uuid),
                ],
                enabled_capabilities={
                    EnabledCapability.DIMMER,
                    EnabledCapability.POSITION,
                    EnabledCapability.COLOUR,
                    EnabledCapability.GOBO,
                    EnabledCapability.BEAM,
                    EnabledCapability.FOCUS,
                },
            )
            f._rebuild_io()
            names = list(f.out_data_types.keys())

            # Alpha's block appears before Bravo's (alphabetical by prefix).
            alpha_block = [n for n in names if n.startswith("Alpha__")]
            bravo_block = [n for n in names if n.startswith("Bravo__")]
            alpha_start = names.index(alpha_block[0])
            bravo_start = names.index(bravo_block[0])
            self.assertLess(alpha_start, bravo_start)
            # And they are contiguous (no interleaving).
            self.assertEqual(alpha_block, names[alpha_start:alpha_start + len(alpha_block)])
            self.assertEqual(bravo_block, names[bravo_start:bravo_start + len(bravo_block)])

            # Alpha has dimmer -> position -> gobo -> beam -> focus (no colour).
            self.assertEqual(
                [
                    "Alpha__brightness",
                    "Alpha__strobefreq",
                    "Alpha__duty_cycle",
                    "Alpha__pan_value",
                    "Alpha__pan_curvesel",
                    "Alpha__tilt_value",
                    "Alpha__tilt_curvesel",
                    "Alpha__goboslot_0",
                    "Alpha__goborotation_0",
                    "Alpha__zoom",
                    "Alpha__focus",
                ],
                alpha_block,
            )

            # Bravo: dimmer, position, colour (no gobo/focus/beam).
            self.assertEqual(
                [
                    "Bravo__brightness",
                    "Bravo__strobefreq",
                    "Bravo__duty_cycle",
                    "Bravo__pan_value",
                    "Bravo__pan_curvesel",
                    "Bravo__tilt_value",
                    "Bravo__tilt_curvesel",
                    "Bravo__color",
                ],
                bravo_block,
            )
        finally:
            del type(scene.board_configuration).fixtures

    def test_mixed_spot_and_wash_scenario_isolates_per_fixture_channels(self) -> None:
        """A Hero Spot 230 and a Hero Wash 640FX enabled with every capability must
        produce only the channels each fixture physically supports:
        - Both get dimmer/position/colour and the shared BEAM zoom channel.
        - Only the spot gets focus and gobo wheels.
        - Neither gets iris (neither physically has one)."""
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType, WheelSlotType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_mixed")

        def _ofl_cap(cap_type):
            cap = MagicMock(); cap.type = cap_type
            return cap

        def _channel(name: str, caps: list):
            template = MagicMock(); template.get_capabilities.return_value = caps
            ch = MagicMock(); ch.name = name; ch.channel_template = template
            return ch

        spot_uuid = "11111111-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        wheel_a = MagicMock(); wheel_a.slots = [gobo_slot]
        wheel_b = MagicMock(); wheel_b.slots = [gobo_slot]
        spot = MagicMock()
        spot.uuid = spot_uuid
        spot.name_on_stage = "Hero Spot"
        spot.fixture_channels = (
            _channel("Pan", [_ofl_cap(CapabilityType.PAN)]),
            _channel("Tilt", [_ofl_cap(CapabilityType.TILT)]),
            _channel("Intensity", [_ofl_cap(CapabilityType.INTENSITY)]),
            _channel("Focus", [_ofl_cap(CapabilityType.FOCUS)]),
            _channel("Zoom", [_ofl_cap(CapabilityType.ZOOM)]),
        )
        spot._fixture = MagicMock()
        spot._fixture.wheels = {"Gobo Wheel": wheel_a, "Rotatable Gobo Wheel": wheel_b}

        wash_uuid = "22222222-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        wash = MagicMock()
        wash.uuid = wash_uuid
        wash.name_on_stage = "Hero Wash"
        wash.fixture_channels = (
            _channel("Pan", [_ofl_cap(CapabilityType.PAN)]),
            _channel("Tilt", [_ofl_cap(CapabilityType.TILT)]),
            _channel("Intensity", [_ofl_cap(CapabilityType.INTENSITY)]),
            _channel("R", [_ofl_cap(CapabilityType.COLOR_INTENSITY)]),
            _channel("G", [_ofl_cap(CapabilityType.COLOR_INTENSITY)]),
            _channel("B", [_ofl_cap(CapabilityType.COLOR_INTENSITY)]),
            _channel("W", [_ofl_cap(CapabilityType.COLOR_INTENSITY)]),
            _channel("Zoom", [_ofl_cap(CapabilityType.ZOOM)]),
        )
        wash._fixture = MagicMock(); wash._fixture.wheels = {}

        type(scene.board_configuration).fixtures = PropertyMock(return_value=[spot, wash])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=spot_uuid),
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=wash_uuid),
                ],
                enabled_capabilities={
                    EnabledCapability.DIMMER,
                    EnabledCapability.POSITION,
                    EnabledCapability.COLOUR,
                    EnabledCapability.GOBO,
                    EnabledCapability.BEAM,
                    EnabledCapability.FOCUS,
                },
            )
            f._rebuild_io()
            channels = set(f.out_data_types)

            # Both fixtures: dimmer, position and zoom (BEAM shared).
            for base in ("Hero_Spot", "Hero_Wash"):
                self.assertIn(f"{base}__brightness", channels)
                self.assertIn(f"{base}__pan_value", channels)
                self.assertIn(f"{base}__tilt_value", channels)
                self.assertIn(f"{base}__zoom", channels)

            # Spot has focus and two gobo wheels.
            self.assertIn("Hero_Spot__focus", channels)
            self.assertIn("Hero_Spot__goboslot_0", channels)
            self.assertIn("Hero_Spot__goborotation_0", channels)
            self.assertIn("Hero_Spot__goboslot_1", channels)
            self.assertIn("Hero_Spot__goborotation_1", channels)

            # Wash has colour.
            self.assertIn("Hero_Wash__color", channels)

            # Wash has no focus and no gobo channels.
            self.assertNotIn("Hero_Wash__focus", channels)
            self.assertNotIn("Hero_Wash__goboslot_0", channels)
            self.assertNotIn("Hero_Wash__goborotation_0", channels)

            # Neither has iris or prism (nothing in the templates).
            for base in ("Hero_Spot", "Hero_Wash"):
                self.assertNotIn(f"{base}__iris", channels)
                self.assertNotIn(f"{base}__prism_selection", channels)
                self.assertNotIn(f"{base}__prism_rotation", channels)
        finally:
            del type(scene.board_configuration).fixtures

    def test_duplicate_stage_names_get_deterministic_uuid_suffix(self) -> None:
        """Two fixtures with the same stage name must produce distinct output
        names via a short, deterministic UUID tail suffix."""
        from unittest.mock import MagicMock, PropertyMock
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_dupnames")
        uuid_a = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"
        uuid_b = "9f752ce5-3a25-4ed0-86f8-31ff47d4e5c9"
        fa = MagicMock(); fa.uuid = uuid_a; fa.name_on_stage = "Hero Spot"
        fb = MagicMock(); fb.uuid = uuid_b; fb.name_on_stage = "Hero Spot"
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[fa, fb])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=uuid_a),
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=uuid_b),
                ],
                enabled_capabilities={EnabledCapability.DIMMER},
            )
            f.property_model.cues.append(PropertyCue(name="C1", steps=[
                PropertyStep(name="s0", duration_40hz=40, assignments={
                    f"fixture:{uuid_a}": _manual_dimmer(0.5),
                    f"fixture:{uuid_b}": _manual_dimmer(0.75),
                }),
            ]))
            f._rebuild_io()
            # Suffix is first 8 hex chars of the dash-stripped UUID.
            self.assertIn("Hero_Spot_30ed4259__brightness", f.out_data_types)
            self.assertIn("Hero_Spot_9f752ce5__brightness", f.out_data_types)
            # Bare "Hero_Spot__brightness" must not appear -- both would collide.
            self.assertNotIn("Hero_Spot__brightness", f.out_data_types)
        finally:
            del type(scene.board_configuration).fixtures

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

    def test_deserialize_preserves_property_model_identity(self) -> None:
        """Regression: UI widgets cache ``filter.property_model`` at construction time.

        If :meth:`deserialize` replaced the model instance, every editor would
        silently keep reading the pre-reload model and the user's data would
        appear to vanish on reopen. In-place mutation keeps the identity stable.
        """
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_identity")
        f.property_model.cues.append(PropertyCue(name="C1"))
        f.serialize()
        pre_model = f.property_model
        f.deserialize()
        self.assertIs(pre_model, f.property_model)
        self.assertEqual("C1", f.property_model.cues[0].name)

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
        # Dimmer capability routes through the strobe generator chain so the
        # brightness port exposes the strobe filter's float output.
        self.assertTrue(
            resolved.endswith("_dimmer_strobe:value"),
            f"brightness output port must come from strobe generator, got: {resolved}",
        )

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
        # Canonical dimmer chain picks the MH1 prefix for the strobe generator.
        self.assertTrue(
            resolved_mh1.endswith("MH1__dimmer_strobe:value"),
            f"canonical brightness must come from MH1 strobe generator, got: {resolved_mh1}",
        )
        # Consolidation collapses MH2 brightness into the MH1 canonical cue
        # filter output; the non-canonical fallback currently references the
        # consolidated cue filter channel directly (compiler-level fallback).
        self.assertIn("MH1__brightness", resolved_mh2)
        # Only one float strobe generator is instantiated because both
        # fixtures share the same consolidated brightness timeline.
        res = f._ensure_compiled()
        strobe_count = sum(
            1 for pf in res.postprocess_filters
            if int(pf.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
        )
        self.assertEqual(1, strobe_count)

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
