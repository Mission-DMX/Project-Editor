"""Per-type assertions for arithmetic filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ArithmeticSubclassTests(unittest.TestCase):
    """Per-type assertions for the native arithmetic subclasses migrated in PR 4.

    Covers the static-I/O arithmetics only. The ``FILTER_SUM_*`` aggregating filters have
    configuration-dependent input counts and will be covered when the aggregating category
    migrates.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_mac_signature_and_defaults(self) -> None:
        """MAC arithmetic filter has factor1/factor2/summand inputs and standard defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC, filter_id="m")
        self.assertEqual(
            f.in_data_types,
            {"factor1": DataType.DT_DOUBLE, "factor2": DataType.DT_DOUBLE, "summand": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.default_values, {"factor1": "1.0", "factor2": "1.0", "summand": "0.0"})
        self.assertFalse(f.configuration_supported)

    def test_float_to_byte_converters(self) -> None:
        """Float-to-16bit and float-to-8bit converters map a double input to the right int type."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f16 = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_16BIT, filter_id="f16"
        )
        f8 = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT, filter_id="f8"
        )
        self.assertEqual(f16.in_data_types, {"value_in": DataType.DT_DOUBLE})
        self.assertEqual(f16.out_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f8.out_data_types, {"value": DataType.DT_8_BIT})

    def test_round_log_exp_signatures(self) -> None:
        """Round/log/exp arithmetic filters share the single-double-in, single-double-out shape."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in (
            FilterTypeEnumeration.FILTER_ARITHMETICS_ROUND,
            FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM,
            FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"a_{ft.name}")
                self.assertEqual(f.in_data_types, {"value_in": DataType.DT_DOUBLE})
                self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        # log has a non-zero default input value to keep ln(0) at bay
        log_f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM, filter_id="l"
        )
        self.assertEqual(log_f.default_values["value_in"], "1")

    def test_min_max_signatures_and_defaults(self) -> None:
        """Min/max arithmetic filters expose param1/param2 inputs and a double ``value`` output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in (
            FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM,
            FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"a_{ft.name}")
                self.assertEqual(
                    f.in_data_types, {"param1": DataType.DT_DOUBLE, "param2": DataType.DT_DOUBLE}
                )
                self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
                self.assertEqual(f.default_values, {"param1": "1", "param2": "1"})
