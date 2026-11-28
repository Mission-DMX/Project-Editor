"""Tests for the ColorToColorWheel virtual filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ColorToColorWheelTests(unittest.TestCase):
    """Per-type assertions for ColorToColorWheel migrated in PR 20."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_and_configs(self) -> None:
        """Default ColorToColorWheel exposes only the color input and 8-bit colorwheel output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_COLOR_TO_COLORWHEEL, filter_id="ccw"
        )
        self.assertEqual(f.filter_configurations["mode"], "automatic")
        # Both dimmer features default to disabled (empty configuration string).
        self.assertEqual(f.filter_configurations["dimmer-input"], "")
        self.assertEqual(f.filter_configurations["dimmer-output"], "")
        self.assertEqual(f.filter_configurations["colorwheel-datatype"], "8bit")
        self.assertEqual(f.in_data_types["input"], DataType.DT_COLOR)
        # Neither dimmer port is exposed until the user opts in via the settings widget.
        self.assertNotIn("in_dimmer", f.in_data_types)
        self.assertNotIn("dimmer", f.out_data_types)
        self.assertEqual(f.out_data_types["colorwheel"], DataType.DT_8_BIT)

    def test_dynamic_dimmer_in_and_out(self) -> None:
        """Enabling dimmer input/output configs adds the typed dimmer ports to the signature."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_COLOR_TO_COLORWHEEL,
            filter_id="ccw",
            filter_configurations={
                "dimmer-input": "float",
                "dimmer-output": "16bit",
                "colorwheel-datatype": "16bit",
            },
        )
        self.assertEqual(f.in_data_types["in_dimmer"], DataType.DT_DOUBLE)
        self.assertEqual(f.out_data_types["dimmer"], DataType.DT_16_BIT)
        self.assertEqual(f.out_data_types["colorwheel"], DataType.DT_16_BIT)

    def test_empty_dimmer_input_drops_in_dimmer_port(self) -> None:
        """An empty ``dimmer-input`` config must not expose the ``in_dimmer`` port."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_COLOR_TO_COLORWHEEL,
            filter_id="ccw",
            filter_configurations={"dimmer-input": ""},
        )
        self.assertNotIn("in_dimmer", f.in_data_types)

    def test_extract_empty_wheel_slot_anchors_to_white(self) -> None:
        """Empty OFL wheel slots must appear at the white anchor (hue=0, saturation=0)."""
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType
        from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

        # A fully defaulted WheelSlot has no distinguishing colour information. ``resulting_color``
        # would route it through ``get_color_by_name("")`` and return black; the filter must
        # override that so the pass-through beam is anchored to white instead.
        empty_slot = WheelSlot()
        red_slot = WheelSlot(type=WheelSlotType.COLOR, name="red")

        class _StubFixture:
            @property
            def colorwheel_mappings(self):
                return [(None, [(10, empty_slot, None), (128, red_slot, None)])]

        self.assertEqual(
            "0.0:0.0:10;0.0:1.0:128",
            extract_colorwheel_mappings_from_fixture(_StubFixture()),
        )

    def test_extract_open_slot_resolves_to_white(self) -> None:
        """Explicit OPEN slots keep their existing white resolution (sanity check)."""
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType
        from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

        open_slot = WheelSlot(type=WheelSlotType.OPEN, name="Open")

        class _StubFixture:
            @property
            def colorwheel_mappings(self):
                return [(None, [(5, open_slot, None)])]

        self.assertEqual("0.0:0.0:5", extract_colorwheel_mappings_from_fixture(_StubFixture()))

    def test_extract_interpolation_slots_are_skipped(self) -> None:
        """Mappings with a second slot (interpolation between two positions) are excluded."""
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType
        from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

        red = WheelSlot(type=WheelSlotType.COLOR, name="red")
        blue = WheelSlot(type=WheelSlotType.COLOR, name="blue")

        class _StubFixture:
            @property
            def colorwheel_mappings(self):
                return [(None, [(20, red, None), (40, red, blue), (60, blue, None)])]

        # The (red, blue) interpolation slot in the middle must be dropped from the output.
        self.assertEqual(
            "0.0:1.0:20;240.0:1.0:60",
            extract_colorwheel_mappings_from_fixture(_StubFixture()),
        )

    def test_extract_returns_empty_string_without_wheels(self) -> None:
        """A fixture without any colour-wheel channels produces an empty mapping string."""
        from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

        class _StubFixture:
            @property
            def colorwheel_mappings(self):
                return []

        self.assertEqual("", extract_colorwheel_mappings_from_fixture(_StubFixture()))

    def test_extract_returns_empty_string_for_none_fixture(self) -> None:
        """Passing ``None`` is a documented no-op that yields an empty mapping string."""
        from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

        self.assertEqual("", extract_colorwheel_mappings_from_fixture(None))

    def test_extract_selects_requested_wheel_index(self) -> None:
        """``selected_slot_index`` chooses between multiple colour wheels on one fixture."""
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType
        from model.virtual_filters.color_to_colorwheel import extract_colorwheel_mappings_from_fixture

        red = WheelSlot(type=WheelSlotType.COLOR, name="red")
        green = WheelSlot(type=WheelSlotType.COLOR, name="green")

        class _StubFixture:
            @property
            def colorwheel_mappings(self):
                return [(None, [(10, red, None)]), (None, [(20, green, None)])]

        self.assertEqual(
            "120.0:1.0:20",
            extract_colorwheel_mappings_from_fixture(_StubFixture(), selected_slot_index=1),
        )
