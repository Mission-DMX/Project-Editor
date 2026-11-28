"""Tests for copying filter instances."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class FilterCopyTests(unittest.TestCase):
    """Guard the ``Filter.copy()`` path which now routes through the unified factory."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_copy_preserves_configuration_and_channel_links(self) -> None:
        """A copied filter owns independent dicts holding the source's values."""
        from model.filter import Filter, FilterTypeEnumeration

        scene = self._make_scene()
        src = Filter(scene, "src", FilterTypeEnumeration.FILTER_CONSTANT_8BIT)
        src.filter_configurations["k"] = "v"
        src.initial_parameters["value"] = "127"
        src.channel_links["in"] = "other:out"

        dst = src.copy(new_id="dst")
        self.assertEqual(dst.filter_id, "dst")
        self.assertEqual(dst.filter_configurations, {"k": "v"})
        self.assertEqual(dst.initial_parameters, {"value": "127"})
        self.assertEqual(dst.channel_links, {"in": "other:out"})
        self.assertIsNot(dst.filter_configurations, src.filter_configurations)
        self.assertIsNot(dst.channel_links, src.channel_links)

    def test_copy_of_virtual_filter_runs_deserialize(self) -> None:
        """Copies of VirtualFilter instances must come back fully populated."""
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.range_adapters import DimmerGlobalBrightnessMixinVFilter

        scene = self._make_scene()
        src = DimmerGlobalBrightnessMixinVFilter(scene, "dbm", (0, 0))
        src.filter_configurations["input_method"] = "8bit"
        src.filter_configurations["input_method_mixin"] = "16bit"

        dst = src.copy(new_id="dbm_copy")
        self.assertEqual(dst.filter_configurations.get("input_method"), "8bit")
        self.assertEqual(dst.filter_configurations.get("input_method_mixin"), "16bit")
        # deserialize() populates _in_data_types from input_method configuration keys
        self.assertIn("input", dst.in_data_types)
        self.assertIn("mixin", dst.in_data_types)
        self.assertEqual(int(dst.filter_type), int(FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN))
