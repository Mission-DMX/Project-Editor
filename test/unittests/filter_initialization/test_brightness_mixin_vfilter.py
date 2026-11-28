"""Tests for the dimmer brightness mixin virtual filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class BrightnessMixinVFilterTests(unittest.TestCase):
    """Per-type assertions for the two brightness-mixin v-filters migrated in PR 19."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_dimmer_mixin_default_signature_matches_default_configs(self) -> None:
        """Default dimmer-mixin configs produce the pre-PR 19 I/O signature."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN, filter_id="d"
        )
        # Default configs chosen to match the pre-PR 19 ``deserialize`` behaviour.
        self.assertEqual(f.filter_configurations["has_8bit_output"], "true")
        self.assertEqual(f.filter_configurations["has_16bit_output"], "false")
        self.assertEqual(f.filter_configurations["input_method"], "16bit")
        self.assertEqual(f.filter_configurations["input_method_mixin"], "8bit")
        # Only enabled outputs are declared so the serializer never walks a port whose
        # backing native filter isn't materialised by ``instantiate_filters``.
        self.assertEqual(f.out_data_types, {"dimmer_out8b": DataType.DT_8_BIT})
        self.assertEqual(f.in_data_types["offset"], DataType.DT_DOUBLE)
        # input defaults to 16bit per the input_method default, mixin to 8bit.
        self.assertEqual(f.in_data_types["input"], DataType.DT_16_BIT)
        self.assertEqual(f.in_data_types["mixin"], DataType.DT_8_BIT)

    def test_dimmer_mixin_output_set_follows_has_output_flags(self) -> None:
        """Toggling ``has_*_output`` adds / removes the corresponding output port."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        both = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN,
            filter_id="d_both",
            filter_configurations={"has_8bit_output": "true", "has_16bit_output": "true"},
        )
        self.assertEqual(
            both.out_data_types,
            {"dimmer_out8b": DataType.DT_8_BIT, "dimmer_out16b": DataType.DT_16_BIT},
        )
        only16 = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN,
            filter_id="d_only16",
            filter_configurations={"has_8bit_output": "false", "has_16bit_output": "true"},
        )
        self.assertEqual(only16.out_data_types, {"dimmer_out16b": DataType.DT_16_BIT})
        neither = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN,
            filter_id="d_neither",
            filter_configurations={"has_8bit_output": "false", "has_16bit_output": "false"},
        )
        self.assertEqual(neither.out_data_types, {})

    def test_dimmer_mixin_input_method_switches_signature(self) -> None:
        """``input_method`` / ``input_method_mixin`` configs choose the input terminal data types."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN,
            filter_id="d",
            filter_configurations={"input_method": "8bit", "input_method_mixin": "16bit"},
        )
        self.assertEqual(f.in_data_types["input"], DataType.DT_8_BIT)
        self.assertEqual(f.in_data_types["mixin"], DataType.DT_16_BIT)

    def test_dimmer_mixin_deserialize_still_rebuilds_io(self) -> None:
        """Backward-compat shim: calling ``deserialize()`` directly must repopulate I/O."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN, filter_id="d"
        )
        f.filter_configurations["input_method"] = "8bit"
        # Explicit call bypasses update_filter_configuration; the shim must still trigger a rebuild.
        f.deserialize()
        self.assertEqual(f.in_data_types["input"], DataType.DT_8_BIT)

    def test_color_brightness_mixin_signature(self) -> None:
        """ColorGlobalBrightnessMixin exposes color_in + brightness inputs and one color output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN, filter_id="c"
        )
        self.assertEqual(
            f.in_data_types,
            {"color_in": DataType.DT_COLOR, "brightness": DataType.DT_8_BIT},
        )
        self.assertEqual(f.out_data_types, {"out": DataType.DT_COLOR})
