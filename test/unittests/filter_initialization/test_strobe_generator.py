"""Per-type assertions for strobe generator filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class StrobeGeneratorSubclassTests(unittest.TestCase):
    """Per-type assertions for the series-strobe-generator subclasses."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_strobe_generator_shared_signature_per_data_type(self) -> None:
        """Each strobe subclass maps brightness/value to its data type and keeps 8-bit controls."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_8BIT, DataType.DT_8_BIT),
            (FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_16BIT, DataType.DT_16_BIT),
            (FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT, DataType.DT_DOUBLE),
        ]
        for ft, expected_dt in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"s_{ft.name}")
                self.assertEqual(f.in_data_types["brightness"], expected_dt)
                self.assertEqual(f.in_data_types["frequency"], DataType.DT_8_BIT)
                self.assertEqual(f.in_data_types["duty_cycle"], DataType.DT_8_BIT)
                self.assertEqual(f.out_data_types, {"value": expected_dt})
                self.assertEqual(f.default_values["brightness"], "0")
                self.assertEqual(f.default_values["frequency"], "0")
                self.assertEqual(f.default_values["duty_cycle"], "128")
                self.assertEqual(f.filter_configurations["slowest_period_ms"], "500.0")
                self.assertEqual(int(f.filter_type), int(ft))

    def test_strobe_generator_preserves_loaded_configuration(self) -> None:
        """A loaded ``slowest_period_ms`` overrides the subclass default."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT,
            filter_id="s",
            filter_configurations={"slowest_period_ms": "250.0", "future_key": "x"},
        )
        self.assertEqual(f.filter_configurations["slowest_period_ms"], "250.0")
        self.assertEqual(f.filter_configurations["future_key"], "x")


if __name__ == "__main__":
    unittest.main()
