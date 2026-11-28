"""Per-type assertions for adapter filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class AdapterSubclassTests(unittest.TestCase):
    """Per-type assertions for the native adapter subclasses migrated in PR 1.

    Each subclass must initialise its I/O signature at construction time, without the
    corresponding node ever being created. Any new migration adds assertions here.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_adapter_16bit_to_dual_8bit_signature(self) -> None:
        """16bit-to-dual-8bit adapter has one 16-bit input and lower/upper 8-bit outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value_lower": DataType.DT_8_BIT, "value_upper": DataType.DT_8_BIT})
        self.assertFalse(f.configuration_supported)

    def test_adapter_16bit_to_bool_signature(self) -> None:
        """16bit-to-bool adapter maps DT_16_BIT in to DT_BOOL out."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_BOOL})
        self.assertFalse(f.configuration_supported)

    def test_adapter_16bit_to_float_signature(self) -> None:
        """16bit-to-float adapter maps DT_16_BIT in to DT_DOUBLE out."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})

    def test_adapter_8bit_to_float_signature(self) -> None:
        """8bit-to-float adapter maps DT_8_BIT in to DT_DOUBLE out."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})

    def test_adapter_color_to_rgb_signature(self) -> None:
        """ColorToRGB adapter has one color input and r/g/b 8-bit outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(
            f.out_data_types,
            {"r": DataType.DT_8_BIT, "g": DataType.DT_8_BIT, "b": DataType.DT_8_BIT},
        )

    def test_adapter_color_to_rgbw_signature(self) -> None:
        """ColorToRGBW adapter exposes r/g/b/w output ports."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW, filter_id="a"
        )
        self.assertEqual(set(f.out_data_types.keys()), {"r", "g", "b", "w"})

    def test_adapter_color_to_rgbwa_signature(self) -> None:
        """ColorToRGBWA adapter exposes r/g/b/w/a output ports."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBWA, filter_id="a"
        )
        self.assertEqual(set(f.out_data_types.keys()), {"r", "g", "b", "w", "a"})

    def test_adapter_float_to_color_signature_and_default_value(self) -> None:
        """FloatToColor adapter has h/s/i float inputs, a color output, and default ``i=1``."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR, filter_id="a"
        )
        self.assertEqual(
            f.in_data_types,
            {"h": DataType.DT_DOUBLE, "s": DataType.DT_DOUBLE, "i": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(f.default_values, {"i": "1"})

    def test_adapter_color_to_float_signature(self) -> None:
        """ColorToFloat adapter has one color input and h/s/i float outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"input": DataType.DT_COLOR})
        self.assertEqual(set(f.out_data_types.keys()), {"h", "s", "i"})

    def test_dual_byte_to_16bit_signature(self) -> None:
        """Dual-byte-to-16bit adapter has lower/upper inputs and a single 16-bit output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT, filter_id="a"
        )
        self.assertEqual(set(f.in_data_types.keys()), {"lower", "upper"})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})

    def test_8bit_to_16bit_signature(self) -> None:
        """8bit-to-16bit adapter maps a DT_8_BIT input to a DT_16_BIT output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})

    def test_float_to_float_range_signature_and_defaults(self) -> None:
        """Float-to-float range adapter exposes a DT_DOUBLE pass-through with 0..1 defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_DOUBLE})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.initial_parameters["lower_bound_in"], "0")
        self.assertEqual(f.initial_parameters["upper_bound_in"], "1")
        self.assertEqual(f.initial_parameters["lower_bound_out"], "0")
        self.assertEqual(f.initial_parameters["upper_bound_out"], "1")
        self.assertEqual(f.initial_parameters["limit_range"], "0")
        self.assertIn("lower_bound_in", f.gui_update_keys)
        self.assertIn("limit_range", f.gui_update_keys)
        self.assertTrue(f.configuration_supported)  # range adapters allow user config

    def test_float_to_8bit_range_defaults(self) -> None:
        """Float-to-8bit range adapter exposes an 8-bit output with 255 upper default."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE, filter_id="a"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_8_BIT})
        self.assertEqual(f.initial_parameters["upper_bound_out"], "255")

    def test_float_to_16bit_range_defaults(self) -> None:
        """Float-to-16bit range adapter exposes a 16-bit output with 65535 upper default."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE, filter_id="a"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f.initial_parameters["upper_bound_out"], "65535")

    def test_loader_initial_parameters_override_subclass_defaults(self) -> None:
        """Loaded ``initial_parameters`` must take precedence over subclass defaults."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE,
            filter_id="a",
            initial_parameters={"upper_bound_out": "100", "custom_future_key": "x"},
        )
        # loaded value wins
        self.assertEqual(f.initial_parameters["upper_bound_out"], "100")
        # unknown-but-loaded keys are preserved on round-trip
        self.assertEqual(f.initial_parameters["custom_future_key"], "x")
        # other defaults still applied
        self.assertEqual(f.initial_parameters["lower_bound_in"], "0")
