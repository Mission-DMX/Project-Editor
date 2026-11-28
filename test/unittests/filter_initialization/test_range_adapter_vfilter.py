"""Tests for the range adapter virtual filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class RangeAdapterVFilterTests(unittest.TestCase):
    """Per-type assertions for the two range-adapter v-filters migrated in PR 18."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_sixteen_bit_to_float_range_signature_and_defaults(self) -> None:
        """16bit-to-float range adapter maps DT_16_BIT in to DT_DOUBLE out with the full defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE, filter_id="r16"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.initial_parameters["lower_bound_in"], "0")
        self.assertEqual(f.initial_parameters["upper_bound_in"], "65535")
        self.assertEqual(f.initial_parameters["lower_bound_out"], "0.0")
        self.assertEqual(f.initial_parameters["upper_bound_out"], "1.0")
        self.assertEqual(f.initial_parameters["limit_range"], "0")
        self.assertIn("lower_bound_in", f.gui_update_keys)
        self.assertIn("limit_range", f.gui_update_keys)

    def test_eight_bit_to_float_range_signature_and_defaults(self) -> None:
        """8bit-to-float range adapter maps DT_8_BIT in to DT_DOUBLE out with 0..255 defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE, filter_id="r8"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.initial_parameters["upper_bound_in"], "255")

    def test_range_adapter_instantiate_produces_initialized_natives(self) -> None:
        """``instantiate_filters()`` now routes through the factory → produced filters have I/O."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        v = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE, filter_id="r"
        )
        v.channel_links["value_in"] = "src:value"
        produced: list = []
        v.instantiate_filters(produced)
        self.assertEqual(len(produced), 2)
        # Each produced native has a populated I/O signature (headless invariant).
        for native in produced:
            self.assertGreater(len(native.in_data_types) + len(native.out_data_types), 0)
        # Specifically the 16bit→float conversion and float→float range mapping.
        self.assertEqual(
            produced[0].out_data_types, {"value": DataType.DT_DOUBLE}
        )
        self.assertEqual(
            produced[1].in_data_types, {"value_in": DataType.DT_DOUBLE}
        )
        # Range filter inherits the v-filter's initial_parameters.
        self.assertEqual(produced[1].initial_parameters["upper_bound_in"], "65535")
