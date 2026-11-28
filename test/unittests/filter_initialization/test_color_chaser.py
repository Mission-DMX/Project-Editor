"""Tests for the color chaser filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ColorChaserTests(unittest.TestCase):
    """Per-type assertions for the ColorChaser subclass migrated in PR 16."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_and_defaults(self) -> None:
        """Default ColorChaser exposes time inputs and one default pixel output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_COLOR_CHASER, filter_id="c"
        )
        self.assertEqual(
            f.in_data_types,
            {"time": DataType.DT_DOUBLE, "time_scale": DataType.DT_DOUBLE},
        )
        # One default pixel output "0".
        self.assertEqual(f.out_data_types, {"0": DataType.DT_COLOR})
        self.assertEqual(f.default_values["time_scale"], "1.0")
        self.assertEqual(f.filter_configurations["number_of_pixels"], "1")
        self.assertEqual(f.filter_configurations["color_parameters"], "")
        self.assertEqual(f.filter_configurations["number_parameters"], "")
        self.assertEqual(f.filter_configurations["presets"], "")
        self.assertEqual(f.filter_configurations["trigger_event"], "")
        self.assertEqual(f.initial_parameters["config"], "")

    def test_dynamic_inputs_and_pixel_outputs(self) -> None:
        """Pixel count and parameter configs populate numbered color outputs and typed inputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_COLOR_CHASER,
            filter_id="c",
            filter_configurations={
                "number_of_pixels": "4",
                "number_parameters": "speed:intensity",
                "color_parameters": "tint",
            },
        )
        self.assertEqual(set(f.out_data_types.keys()), {"0", "1", "2", "3"})
        for key in ("0", "1", "2", "3"):
            self.assertEqual(f.out_data_types[key], DataType.DT_COLOR)
        self.assertEqual(f.in_data_types["speed"], DataType.DT_16_BIT)
        self.assertEqual(f.in_data_types["intensity"], DataType.DT_16_BIT)
        self.assertEqual(f.in_data_types["tint"], DataType.DT_COLOR)
        self.assertEqual(f.default_values["speed"], "0")
        self.assertEqual(f.default_values["tint"], "360.0,1.0,1.0")

    def test_malformed_pixel_count_clamps_to_zero(self) -> None:
        """A non-numeric ``number_of_pixels`` config degrades to zero outputs."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_COLOR_CHASER,
            filter_id="c",
            filter_configurations={"number_of_pixels": "garbage"},
        )
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.filter_configurations["number_of_pixels"], "0")

    def test_chaser_node_syncs_terminals_on_settings_change(self) -> None:
        """Dynamic rebuild: start with one pixel, grow to three, shrink to one."""
        from view.show_mode.editor.nodes.impl.effects import ChaserNode

        scene = self._make_scene()
        node = ChaserNode(model=scene, name="c")
        self.assertEqual(set(node.outputs().keys()), {"0"})
        self.assertEqual(set(node.inputs().keys()), {"time", "time_scale"})
        node.filter.filter_configurations["number_of_pixels"] = "3"
        node.filter.filter_configurations["number_parameters"] = "freq"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.outputs().keys()), {"0", "1", "2"})
        self.assertEqual(set(node.inputs().keys()), {"time", "time_scale", "freq"})
        node.filter.filter_configurations["number_of_pixels"] = "1"
        node.filter.filter_configurations["number_parameters"] = ""
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.outputs().keys()), {"0"})
        self.assertEqual(set(node.inputs().keys()), {"time", "time_scale"})
