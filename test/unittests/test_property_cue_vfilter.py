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
    """Re-enable the garbage collector after the module finishes."""
    gc.enable()


def _make_scene():
    """Return a fresh Scene wired into a BoardConfiguration for use in tests."""
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
    """Tests for the PropertyBasedCueFilter vfilter shell."""

    def test_default_empty_io(self) -> None:
        """Verify a freshly constructed filter has the expected default input types and empty outputs."""
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_default")
        self.assertEqual(DataType.DT_DOUBLE, f.in_data_types["time"])
        self.assertEqual(DataType.DT_DOUBLE, f.in_data_types["time_scale"])
        self.assertEqual("1.0", f.default_values["time_scale"])
        self.assertEqual({}, f.out_data_types)
        self.assertIn("cues-prop-data", f.filter_configurations)

    def test_rebuild_io_populates_outputs_from_model(self) -> None:
        """Verify rebuilt outputs reflect compiled channels from the model.

        After the model carries a configured fixture + assignment, the
        vfilter's ``out_data_types`` must reflect the compiled channels so the
        pyqtgraph node can grow terminals for them.
        """
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
        """Verify output channel names use the fixture's stage name when the board knows it.

        When a fixture's UUID resolves to a stage name on the board, output
        channels should carry that readable name instead of the raw UUID.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_names")
        fixture_uuid = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"
        mock_fixture = MagicMock()
        mock_fixture.uuid = fixture_uuid
        mock_fixture.name_on_stage = "Hero Spot 1"
        # Give the fixture a single INTENSITY channel so capability discovery
        # reports DIMMER -- the per-fixture-capability filter in ``_collect_cue``
        # now requires that the physical fixture actually supports a property
        # before emitting channels for it.
        _intensity_cap = MagicMock(); _intensity_cap.type = CapabilityType.INTENSITY
        _intensity_template = MagicMock()
        _intensity_template.get_capabilities.return_value = [_intensity_cap]
        _intensity_channel = MagicMock()
        _intensity_channel.name = "Intensity"
        _intensity_channel.channel_template = _intensity_template
        mock_fixture.fixture_channels = (_intensity_channel,)
        mock_fixture._fixture = MagicMock(); mock_fixture._fixture.wheels = {}
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

    def test_synthesized_pan_tilt_outputs_are_16bit(self) -> None:
        """Verify synthesized pan/tilt outputs carry the 16-bit data type.

        ``pan`` and ``tilt`` on the node come from the 16-bit range adapter
        in the post-processing chain -- not from the raw ``*_value`` float.
        """
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_pantype")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.POSITION},
        )
        f._rebuild_io()
        self.assertEqual(DataType.DT_16_BIT, f.out_data_types["MH1__pan"])
        self.assertEqual(DataType.DT_16_BIT, f.out_data_types["MH1__tilt"])

    def test_enabled_capability_exposes_channels_even_without_assignment(self) -> None:
        """Verify enabling a capability exposes channels even without a user assignment.

        Enabling POSITION on a fixture must create pan/tilt output channels
        even when the user hasn't yet dialed in a value. The internal raw
        channels (pan_value/pan_curvesel/strobefreq/...) stay hidden -- they
        exist to drive post-processing filters only.
        """
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_defaults")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.POSITION},
        )
        # No cue, no assignment -- just the enabled capabilities.
        f._rebuild_io()
        for channel in ("MH1__brightness", "MH1__pan", "MH1__tilt"):
            self.assertIn(channel, f.out_data_types, f"missing {channel}")
        for internal in (
            "MH1__strobefreq", "MH1__duty_cycle",
            "MH1__pan_value", "MH1__pan_curvesel",
            "MH1__tilt_value", "MH1__tilt_curvesel",
        ):
            self.assertNotIn(internal, f.out_data_types, f"{internal} should be hidden")

    def test_capability_lookup_restricts_to_supported_capabilities(self) -> None:
        """Verify capability lookup restricts channels to those the fixture physically supports.

        A fixture without a gobo wheel must not expose gobo channels even
        when the user enabled GOBO on the global selection (wash fixtures).
        """
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
                enabled_capabilities={EnabledCapability.COLOR, EnabledCapability.GOBO},
            )
            f._rebuild_io()
            self.assertIn("Hero_Wash__color", f.out_data_types)
            self.assertNotIn("Hero_Wash__goboslot_0", f.out_data_types)
            self.assertNotIn("Hero_Wash__goborotation_0", f.out_data_types)
        finally:
            del type(scene.board_configuration).fixtures

    def test_gobo_wheel_count_lookup_feeds_multiple_wheel_pairs(self) -> None:
        """Verify a fixture with two gobo wheels exposes channels for both wheel pairs.

        A Hero-Spot-style fixture with two gobo wheels must expose channels
        for both wheels, not just wheel 0.
        """
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
        """Verify output terminals are ordered by fixture, then property group, then channel.

        Output terminals must be grouped alphabetically by fixture, then by
        property group (dimmer, position, colour, gobo, beam, focus, frost),
        then within property by the natural channel order so a human can scan
        them top-to-bottom.
        """
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
                    EnabledCapability.COLOR,
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
            # Raw plumbing (strobefreq, duty_cycle, pan_value, pan_curvesel,
            # tilt_value, tilt_curvesel) is hidden; the post-processed pan/tilt
            # terminals appear instead.
            self.assertEqual(
                [
                    "Alpha__brightness",
                    "Alpha__pan",
                    "Alpha__tilt",
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
                    "Bravo__pan",
                    "Bravo__tilt",
                    "Bravo__color",
                ],
                bravo_block,
            )
        finally:
            del type(scene.board_configuration).fixtures

    def test_mixed_spot_and_wash_scenario_isolates_per_fixture_channels(self) -> None:
        """Verify a mixed spot+wash scenario emits only each fixture's supported channels.

        A Hero Spot 230 and a Hero Wash 640FX enabled with every capability must
        produce only the channels each fixture physically supports:
        - Both get dimmer/position/colour and the shared BEAM zoom channel.
        - Only the spot gets focus and gobo wheels.
        - Neither gets iris (neither physically has one).
        """
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
                    EnabledCapability.COLOR,
                    EnabledCapability.GOBO,
                    EnabledCapability.BEAM,
                    EnabledCapability.FOCUS,
                },
            )
            f._rebuild_io()
            channels = set(f.out_data_types)

            # Both fixtures: dimmer, position (post-processed) and zoom (BEAM shared).
            for base in ("Hero_Spot", "Hero_Wash"):
                self.assertIn(f"{base}__brightness", channels)
                self.assertIn(f"{base}__pan", channels)
                self.assertIn(f"{base}__tilt", channels)
                self.assertIn(f"{base}__zoom", channels)
                # Raw plumbing never surfaces on the node.
                self.assertNotIn(f"{base}__pan_value", channels)
                self.assertNotIn(f"{base}__pan_curvesel", channels)
                self.assertNotIn(f"{base}__tilt_value", channels)
                self.assertNotIn(f"{base}__strobefreq", channels)
                self.assertNotIn(f"{base}__duty_cycle", channels)

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

    def test_step_level_gobo_skips_fixtures_without_gobo_wheels(self) -> None:
        """Verify step-level gobo assignments only emit channels on gobo-capable fixtures.

        A step-level gobo assignment (``node_path=""``) must only create
        gobo channels on fixtures that physically have gobo wheels.

        Regression test for a bug where a Hero Spot + Hero Wash setup with a
        step-level gobo assignment (wheel_count=2 dialed in on the spot)
        would also produce ``goboslot_0 / goborotation_0 / goboslot_1 /
        goborotation_1`` on the wash because ``_collect_cue`` did not re-apply
        the per-fixture capability filter.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType, WheelSlotType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_step_gobo")

        def _ofl_cap(cap_type):
            cap = MagicMock(); cap.type = cap_type
            return cap

        def _channel(name: str, caps: list):
            template = MagicMock(); template.get_capabilities.return_value = caps
            ch = MagicMock(); ch.name = name; ch.channel_template = template
            return ch

        spot_uuid = "33333333-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        wheel_a = MagicMock(); wheel_a.slots = [gobo_slot]
        wheel_b = MagicMock(); wheel_b.slots = [gobo_slot]
        spot = MagicMock()
        spot.uuid = spot_uuid
        spot.name_on_stage = "Hero Spot"
        spot.fixture_channels = (
            _channel("Intensity", [_ofl_cap(CapabilityType.INTENSITY)]),
        )
        spot._fixture = MagicMock()
        spot._fixture.wheels = {"Gobo Wheel": wheel_a, "Rotatable Gobo Wheel": wheel_b}

        wash_uuid = "44444444-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        wash = MagicMock()
        wash.uuid = wash_uuid
        wash.name_on_stage = "Hero Wash"
        wash.fixture_channels = (
            _channel("Intensity", [_ofl_cap(CapabilityType.INTENSITY)]),
        )
        wash._fixture = MagicMock(); wash._fixture.wheels = {}

        type(scene.board_configuration).fixtures = PropertyMock(return_value=[spot, wash])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=spot_uuid),
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=wash_uuid),
                ],
                enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.GOBO},
            )
            # Step-level gobo assignment mirroring what the editor emits when
            # the user dials in both wheels of the spot and applies at step
            # level: wheel_count=2 is carried in ``values`` and would normally
            # override the per-fixture wheel_count=0 for the wash.
            step_level_gobo = PropertyAssignments(
                by_property={
                    "gobo": ManualPropertyAssignment(
                        values={
                            "wheel_count": 2,
                            "slots": {0: 0, 1: 3},
                            "rotations": {0: 0.0, 1: 0.0},
                        },
                    ),
                },
            )
            f.property_model.cues.append(PropertyCue(name="C1", steps=[
                PropertyStep(name="s0", duration_40hz=40, assignments={
                    "": step_level_gobo,
                }),
            ]))
            f._rebuild_io()
            channels = set(f.out_data_types)
            # Spot has both gobo wheel pairs.
            self.assertIn("Hero_Spot__goboslot_0", channels)
            self.assertIn("Hero_Spot__goborotation_0", channels)
            self.assertIn("Hero_Spot__goboslot_1", channels)
            self.assertIn("Hero_Spot__goborotation_1", channels)
            # Wash must NOT gain gobo channels just because it shared the
            # step-level assignment with the spot.
            self.assertNotIn("Hero_Wash__goboslot_0", channels)
            self.assertNotIn("Hero_Wash__goborotation_0", channels)
            self.assertNotIn("Hero_Wash__goboslot_1", channels)
            self.assertNotIn("Hero_Wash__goborotation_1", channels)
        finally:
            del type(scene.board_configuration).fixtures

    def test_single_segment_color_fixture_keeps_bare_color_channel(self) -> None:
        """A one-RGB-segment fixture must expose the compact ``color`` port.

        Single-pixel colour fixtures keep the historical bare ``color``
        output name so existing channel-link bindings resolve.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_1seg")
        fid = "55555555-cccc-cccc-cccc-cccccccccccc"

        def _channel(name: str, cap_type):
            cap = MagicMock(); cap.type = cap_type
            template = MagicMock(); template.get_capabilities.return_value = [cap]
            ch = MagicMock(); ch.name = name; ch.channel_template = template
            return ch

        fixture = MagicMock()
        fixture.uuid = fid
        fixture.name_on_stage = "RGB Par"
        fixture.fixture_channels = (
            _channel("Red", CapabilityType.COLOR_INTENSITY),
            _channel("Green", CapabilityType.COLOR_INTENSITY),
            _channel("Blue", CapabilityType.COLOR_INTENSITY),
        )
        fixture._fixture = MagicMock(); fixture._fixture.wheels = {}
        # One RGB segment: one entry in each of the RED/GREEN/BLUE arrays.
        fixture.get_segment_in_universe_by_type = lambda t: (0,) if t.name in ("RED", "GREEN", "BLUE") else ()
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[fixture])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=fid)],
                enabled_capabilities={EnabledCapability.COLOR},
            )
            f._rebuild_io()
            self.assertIn("RGB_Par__color", f.out_data_types)
            self.assertNotIn("RGB_Par__color_0", f.out_data_types)
        finally:
            del type(scene.board_configuration).fixtures

    def test_multi_segment_color_fixture_emits_color_n_channels(self) -> None:
        """Verify a multi-segment RGB fixture exposes color_N channels instead of bare color.

        A 3-segment RGB fixture must expose ``color_0 .. color_2`` and
        not the bare ``color`` name.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_3seg")
        fid = "66666666-dddd-dddd-dddd-dddddddddddd"

        def _channel(name: str, cap_type):
            cap = MagicMock(); cap.type = cap_type
            template = MagicMock(); template.get_capabilities.return_value = [cap]
            ch = MagicMock(); ch.name = name; ch.channel_template = template
            return ch

        fixture = MagicMock()
        fixture.uuid = fid
        fixture.name_on_stage = "LED Bar"
        fixture.fixture_channels = (
            _channel("Red 1", CapabilityType.COLOR_INTENSITY),
            _channel("Green 1", CapabilityType.COLOR_INTENSITY),
            _channel("Blue 1", CapabilityType.COLOR_INTENSITY),
            _channel("Red 2", CapabilityType.COLOR_INTENSITY),
            _channel("Green 2", CapabilityType.COLOR_INTENSITY),
            _channel("Blue 2", CapabilityType.COLOR_INTENSITY),
            _channel("Red 3", CapabilityType.COLOR_INTENSITY),
            _channel("Green 3", CapabilityType.COLOR_INTENSITY),
            _channel("Blue 3", CapabilityType.COLOR_INTENSITY),
        )
        fixture._fixture = MagicMock(); fixture._fixture.wheels = {}
        # Three segments per RGB colour.
        fixture.get_segment_in_universe_by_type = (
            lambda t: (0, 3, 6) if t.name in ("RED", "GREEN", "BLUE") else ()
        )
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[fixture])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=fid)],
                enabled_capabilities={EnabledCapability.COLOR},
            )
            f._rebuild_io()
            channels = set(f.out_data_types)
            self.assertIn("LED_Bar__color_0", channels)
            self.assertIn("LED_Bar__color_1", channels)
            self.assertIn("LED_Bar__color_2", channels)
            self.assertNotIn("LED_Bar__color", channels)
        finally:
            del type(scene.board_configuration).fixtures

    def test_step_level_color_skips_fixtures_without_color(self) -> None:
        """Verify step-level colour assignments only emit channels on colour-capable fixtures.

        A step-level (``node_path=""``) colour assignment with a mixed
        selection must only emit ``color*`` channels on colour-capable
        fixtures. Regression analogue of the step-level gobo fix.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.color_hsi import ColorHSI
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_step_color")

        def _channel(name: str, cap_type):
            cap = MagicMock(); cap.type = cap_type
            template = MagicMock(); template.get_capabilities.return_value = [cap]
            ch = MagicMock(); ch.name = name; ch.channel_template = template
            return ch

        rgb_uuid = "77777777-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        rgb = MagicMock()
        rgb.uuid = rgb_uuid
        rgb.name_on_stage = "RGB Par"
        rgb.fixture_channels = (
            _channel("Red", CapabilityType.COLOR_INTENSITY),
            _channel("Green", CapabilityType.COLOR_INTENSITY),
            _channel("Blue", CapabilityType.COLOR_INTENSITY),
        )
        rgb._fixture = MagicMock(); rgb._fixture.wheels = {}
        rgb.get_segment_in_universe_by_type = (
            lambda t: (0,) if t.name in ("RED", "GREEN", "BLUE") else ()
        )

        dim_uuid = "88888888-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        dim = MagicMock()
        dim.uuid = dim_uuid
        dim.name_on_stage = "Blinder"
        dim.fixture_channels = (_channel("Intensity", CapabilityType.INTENSITY),)
        dim._fixture = MagicMock(); dim._fixture.wheels = {}
        dim.get_segment_in_universe_by_type = lambda _t: ()

        type(scene.board_configuration).fixtures = PropertyMock(return_value=[rgb, dim])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=rgb_uuid),
                    FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=dim_uuid),
                ],
                enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.COLOR},
            )
            step_level_color = PropertyAssignments(
                by_property={
                    "color": ManualPropertyAssignment(
                        values={"colors": {0: ColorHSI(0.0, 1.0, 1.0)}},
                    ),
                },
            )
            f.property_model.cues.append(PropertyCue(name="C1", steps=[
                PropertyStep(name="s0", duration_40hz=40, assignments={
                    "": step_level_color,
                }),
            ]))
            f._rebuild_io()
            channels = set(f.out_data_types)
            # RGB fixture gains the colour channel.
            self.assertIn("RGB_Par__color", channels)
            # Dimmer-only fixture must NOT gain a colour channel.
            self.assertNotIn("Blinder__color", channels)
            self.assertNotIn("Blinder__color_0", channels)
        finally:
            del type(scene.board_configuration).fixtures

    def test_duplicate_stage_names_get_deterministic_uuid_suffix(self) -> None:
        """Verify duplicate stage names are disambiguated via a deterministic UUID suffix.

        Two fixtures with the same stage name must produce distinct output
        names via a short, deterministic UUID tail suffix.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_dupnames")
        uuid_a = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"
        uuid_b = "9f752ce5-3a25-4ed0-86f8-31ff47d4e5c9"

        def _intensity_channel() -> MagicMock:
            cap = MagicMock(); cap.type = CapabilityType.INTENSITY
            template = MagicMock(); template.get_capabilities.return_value = [cap]
            ch = MagicMock(); ch.name = "Intensity"; ch.channel_template = template
            return ch

        fa = MagicMock(); fa.uuid = uuid_a; fa.name_on_stage = "Hero Spot"
        fa.fixture_channels = (_intensity_channel(),)
        fa._fixture = MagicMock(); fa._fixture.wheels = {}
        fb = MagicMock(); fb.uuid = uuid_b; fb.name_on_stage = "Hero Spot"
        fb.fixture_channels = (_intensity_channel(),)
        fb._fixture = MagicMock(); fb._fixture.wheels = {}
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

    def test_sanitize_strips_punctuation_without_partition_breakage(self) -> None:
        """Regression: a name containing ``#`` must not produce ``__`` after sanitisation.

        The previous sanitiser replaced every non-alphanumeric character with
        ``_``, so "Hero Spot #3" became "Hero_Spot__3" — a prefix that then
        broke the compiler's ``partition("__")`` splits and silently dropped
        the fixture's post-processing chain. The shared sanitiser strips
        ``#`` entirely so the prefix becomes "Hero_Spot_3" with no double
        underscore, and the chain publishes a ``brightness`` port.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_hash_name")
        uid = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"

        cap = MagicMock(); cap.type = CapabilityType.INTENSITY
        template = MagicMock(); template.get_capabilities.return_value = [cap]
        ch = MagicMock(); ch.name = "Intensity"; ch.channel_template = template

        fx = MagicMock(); fx.uuid = uid; fx.name_on_stage = "Hero Spot #3"
        fx.fixture_channels = (ch,)
        fx._fixture = MagicMock(); fx._fixture.wheels = {}
        type(scene.board_configuration).fixtures = PropertyMock(return_value=[fx])
        try:
            f.property_model.fixture_selection = FixtureSelection(
                entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=uid)],
                enabled_capabilities={EnabledCapability.DIMMER},
            )
            f.property_model.cues.append(PropertyCue(name="C1", steps=[
                PropertyStep(name="s0", duration_40hz=40,
                             assignments={f"fixture:{uid}": _manual_dimmer(0.5)}),
            ]))
            f._rebuild_io()
            self.assertIn("Hero_Spot_3__brightness", f.out_data_types)
        finally:
            del type(scene.board_configuration).fixtures

    def test_sanitize_dash_and_space_are_distinct(self) -> None:
        """Regression: "MH 1" sanitises to "MH_1" and "MH-1" stays "MH-1".

        The old sanitiser mapped every non-alphanumeric character — including
        ``-`` — to ``_``, so both names collapsed to "MH_1" and the second
        fixture silently overwrote the first. The shared sanitiser leaves
        ``-`` alone, so the two prefixes stay distinct without needing a
        UUID suffix.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_dash_space")
        uuid_a = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"
        uuid_b = "9f752ce5-3a25-4ed0-86f8-31ff47d4e5c9"

        def _intensity_channel() -> MagicMock:
            cap = MagicMock(); cap.type = CapabilityType.INTENSITY
            template = MagicMock(); template.get_capabilities.return_value = [cap]
            ch = MagicMock(); ch.name = "Intensity"; ch.channel_template = template
            return ch

        fa = MagicMock(); fa.uuid = uuid_a; fa.name_on_stage = "MH 1"
        fa.fixture_channels = (_intensity_channel(),)
        fa._fixture = MagicMock(); fa._fixture.wheels = {}
        fb = MagicMock(); fb.uuid = uuid_b; fb.name_on_stage = "MH-1"
        fb.fixture_channels = (_intensity_channel(),)
        fb._fixture = MagicMock(); fb._fixture.wheels = {}
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
                    f"fixture:{uuid_a}": _manual_dimmer(0.25),
                    f"fixture:{uuid_b}": _manual_dimmer(0.75),
                }),
            ]))
            f._rebuild_io()
            channels = set(f.out_data_types)
            self.assertIn("MH_1__brightness", channels)
            self.assertIn("MH-1__brightness", channels)
        finally:
            del type(scene.board_configuration).fixtures

    def test_sanitize_detects_post_sanitisation_collisions(self) -> None:
        """Regression: names differing only in stripped characters get UUID suffixes.

        The sanitiser strips ``#``, ``:`` and ``|``, so "MH#1" and "MH:1" both
        collapse to "MH1". Without post-sanitisation collision detection the
        second fixture would silently overwrite the first's output. The fix
        counts collisions on the sanitised form and adds a deterministic
        UUID suffix to each colliding fixture.
        """
        from unittest.mock import MagicMock, PropertyMock
        from model.ofl.ofl_fixture import CapabilityType
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_sanitise_coll")
        uuid_a = "30ed4259-e513-4c9e-87ef-bf822a46b2c5"
        uuid_b = "9f752ce5-3a25-4ed0-86f8-31ff47d4e5c9"

        def _intensity_channel() -> MagicMock:
            cap = MagicMock(); cap.type = CapabilityType.INTENSITY
            template = MagicMock(); template.get_capabilities.return_value = [cap]
            ch = MagicMock(); ch.name = "Intensity"; ch.channel_template = template
            return ch

        fa = MagicMock(); fa.uuid = uuid_a; fa.name_on_stage = "MH#1"
        fa.fixture_channels = (_intensity_channel(),)
        fa._fixture = MagicMock(); fa._fixture.wheels = {}
        fb = MagicMock(); fb.uuid = uuid_b; fb.name_on_stage = "MH:1"
        fb.fixture_channels = (_intensity_channel(),)
        fb._fixture = MagicMock(); fb._fixture.wheels = {}
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
                    f"fixture:{uuid_a}": _manual_dimmer(0.25),
                    f"fixture:{uuid_b}": _manual_dimmer(0.75),
                }),
            ]))
            f._rebuild_io()
            channels = set(f.out_data_types)
            brightness_ports = [c for c in channels if "__brightness" in c]
            self.assertEqual(2, len(brightness_ports),
                             f"Expected 2 brightness ports, got {brightness_ports}")
            self.assertNotIn("MH1__brightness", channels,
                             "Bare collision name must not appear — one fixture would lose")
        finally:
            del type(scene.board_configuration).fixtures

    def test_roundtrip_configuration(self) -> None:
        """Verify serialising and deserialising a filter preserves cues and assignments."""
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
        """Verify an output port resolves through the strobe generator for a dimmer passthrough."""
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
        """Verify consolidated sibling fixtures share a single canonical strobe output."""
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
        # Both fixtures' brightness ports resolve to the one canonical strobe
        # generator. Previously MH2's port fell through to the native cue
        # filter channel, which quietly bypassed strobe gating for the
        # consolidated sibling -- the rename of the raw channel to
        # ``brightness_raw`` (plus the external-port sharing in ``_build_ports``)
        # routes both prefixes through the MH1 strobe instead.
        self.assertTrue(
            resolved_mh1.endswith("MH1__dimmer_strobe:value"),
            f"canonical brightness must come from MH1 strobe generator, got: {resolved_mh1}",
        )
        self.assertEqual(
            resolved_mh1, resolved_mh2,
            "consolidated sibling brightness must share the canonical strobe output",
        )
        # Only one float strobe generator is instantiated because both
        # fixtures share the same consolidated brightness timeline.
        res = f._ensure_compiled()
        strobe_count = sum(
            1 for pf in res.postprocess_filters
            if int(pf.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
        )
        self.assertEqual(1, strobe_count)

    def test_preview_mode_builds_constant_mapping(self) -> None:
        """Verify preview-mode instantiation builds filters and populates the channel mapping."""
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
        """Verify the vfilter factory constructs a PropertyBasedCueFilter instance."""
        from model.virtual_filters.vfilter_factory import (
            _construct_virtual_filter_instance_legacy,
        )

        scene = _make_scene()
        instance = _construct_virtual_filter_instance_legacy(
            scene, int(FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES), "test_id",
        )
        self.assertIsInstance(instance, PropertyBasedCueFilter)

    def test_postprocess_filters_have_no_self_links_after_serialisation(self) -> None:
        """Regression + invariant guard.

        Reproduces the self-link bug uncovered in
        ``/tmp/fish_scene_parsing_failure.log``: a show-file containing the
        property-cue vfilter wired to a native downstream filter failed to
        schedule in fish because the dimmer strobe filter ended up with its
        own ``:value`` output as one of its inputs. The cause was
        ``filter_serialization.py``'s channel-override dictionary rewriting
        the strategy's internal reference
        ``Property Cues.0:<prefix>__brightness`` to the strategy's own
        output, since the raw channel name and the exposed port name were
        identical.

        The test enables DIMMER + POSITION on a bare fixture id, elaborates
        the vfilter into native filters, replays the exact override rule
        that ``controller.file.serializing.filter_serialization`` applies at
        show-file write time, and asserts that no instantiated filter has a
        ``channel_link`` whose rewritten source references its own
        ``filter_id``. This catches **any** future strategy that accidentally
        publishes an external port name that collides with a raw channel
        name on the native cue filter -- not just the specific dimmer case.
        """
        scene = _make_scene()
        fid = "FX"
        pcf = PropertyBasedCueFilter(scene, "PCF.0")
        pcf.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id=fid)],
            enabled_capabilities={EnabledCapability.DIMMER, EnabledCapability.POSITION},
        )
        pcf.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40, assignments={
                f"fixture:{fid}": _manual_dimmer(0.5),
            }),
        ]))
        pcf._rebuild_io()

        # Elaborate the vfilter into its native filter list, exactly as the
        # serializer does in ``_create_filter_element_for_fish``.
        instantiated: list = []
        pcf.instantiate_filters(instantiated)

        # Build the channel_override_dict the same way the serializer does:
        # one entry per output port exposed on the vfilter node.
        override: dict[str, str] = {}
        for output_port in pcf.out_data_types:
            resolved = pcf.resolve_output_port_id(output_port)
            self.assertIsNotNone(
                resolved,
                f"vfilter must resolve each exposed output port; "
                f"{output_port!r} returned None",
            )
            override[f"{pcf.filter_id}:{output_port}"] = resolved

        # Walk every instantiated filter's channel_links, apply the override
        # that the serializer would apply at write time, and record any
        # filter that ends up with a source reference pointing at itself.
        offenders: list[tuple[str, str, str]] = []
        for filt in instantiated:
            for input_port, source in filt.channel_links.items():
                rewritten = override.get(source, source)
                src_filter = rewritten.partition(":")[0]
                if src_filter == filt.filter_id:
                    offenders.append((filt.filter_id, input_port, rewritten))
        self.assertEqual(
            [], offenders,
            "Found post-processing filters whose channel_links resolve to their "
            "own output after the vfilter's channel_override_dict is applied. "
            "Each entry is (filter_id, input_port, rewritten_source). This means "
            "a strategy publishes an external port name that collides with a raw "
            "channel name on the native cue filter -- the serializer rewrites the "
            "strategy's own internal input to point at its own output, which fish "
            "then rejects at schedule time. Rename the raw channel, add it to "
            "INTERNAL_LOCAL_NAMES, and expose the external name via "
            "SYNTHESIZED_OUTPUTS (see brightness_raw/brightness or "
            "pan_value/pan for the pattern).",
        )

    def test_native_cue_filter_inherits_vfilter_input_wiring(self) -> None:
        """Verify the native cue filter inherits time wiring and omits editor-only blobs.

        The native cue filter must carry the vfilter's ``time`` /
        ``time_scale`` channel_links, gui_update_keys and in_data_types,
        or fish rejects configuration with
        'channel mapping does not contain channel time of type double'.
        The vfilter's editor-only ``cues-prop-data`` blob must NOT leak
        into the native filter configuration sent to fish.
        """
        scene = _make_scene()
        f = PropertyBasedCueFilter(scene, "pcf_wire")
        f.property_model.fixture_selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        f.property_model.cues.append(PropertyCue(name="C1", steps=[
            PropertyStep(name="s0", duration_40hz=40,
                         assignments={"fixture:MH1": _manual_dimmer(0.5)}),
        ]))
        f.channel_links["time"] = "Time.0:value"
        f.channel_links["time_scale"] = "ConstScale.0:value"
        f._rebuild_io()

        instantiated: list = []
        f.instantiate_filters(instantiated)
        native = next(
            (flt for flt in instantiated if flt.filter_id == f.filter_id),
            None,
        )
        self.assertIsNotNone(native, "the native cue filter must be in the instantiated list")
        self.assertEqual("Time.0:value", native.channel_links.get("time"))
        self.assertEqual("ConstScale.0:value", native.channel_links.get("time_scale"))
        self.assertEqual(DataType.DT_DOUBLE, native.in_data_types.get("time"))
        self.assertEqual(DataType.DT_DOUBLE, native.in_data_types.get("time_scale"))
        self.assertIn("run_mode", native.gui_update_keys)
        self.assertIn("run_cue", native.gui_update_keys)
        # The native cue configuration carries fish-facing entries only.
        self.assertIn("cuelist", native.filter_configurations)
        self.assertIn("mapping", native.filter_configurations)
        # The editor-only payload must not travel to fish.
        self.assertNotIn("cues-prop-data", native.filter_configurations)

    def test_compiler_rejects_strategy_that_shadows_raw_channel(self) -> None:
        """Verify the compiler refuses a strategy whose external port shadows a raw channel.

        Direct check on the compile-time invariant that catches the class
        of bug.

        If a post-processing strategy publishes an external port with the
        same local name as a raw channel on the native cue filter,
        ``_build_ports`` must refuse to produce a ``CompileResult``. Without
        this invariant, the bug slips through to the serialiser and manifests
        only when fish rejects the show.
        """
        from unittest.mock import patch

        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.postprocess import PostprocessOutput

        selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="FX")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        scene = _make_scene()
        pcf = PropertyBasedCueFilter(scene, "PCF.0")
        pcf.property_model.fixture_selection = selection

        def _shadowing_strategy(cap: str, ctx):
            if cap != "dimmer":
                # Fall back to passthrough for any other capability.
                return PostprocessOutput(
                    filters=(),
                    external_ports={cap: (ctx.cue_filter_id, f"{ctx.channel_name_prefix}__{cap}")},
                )
            # Build a token filter and expose a port named ``brightness_raw``
            # which collides with the native cue filter's raw channel.
            from model.filter import Filter as _Filter
            from model.filter import FilterTypeEnumeration as _FTE
            token = _Filter(
                ctx.scene, f"{ctx.cue_filter_id}__{ctx.channel_name_prefix}__bad",
                filter_type=_FTE.FILTER_CONSTANT_FLOAT, pos=ctx.pos,
            )
            return PostprocessOutput(
                filters=(token,),
                external_ports={"brightness_raw": (token.filter_id, "value")},
            )

        with patch("model.virtual_filters.property_cues.compiler.build_postprocess_chain",
                   _shadowing_strategy):
            with self.assertRaisesRegex(ValueError, "brightness_raw"):
                compile_property_model(pcf.property_model, "PCF.0", pcf.scene)


if __name__ == "__main__":
    unittest.main()
