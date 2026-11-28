"""Per-type assertions for aggregating filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class AggregatingSubclassTests(unittest.TestCase):
    """Per-type assertions for the native aggregating subclasses migrated in PR 9.

    The virtual-filter ``VFILTER_COLOR_MIXER`` keeps its node-side aggregating behaviour
    until the v-filter pass and is not covered here.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_input_count_populates_two_inputs(self) -> None:
        """Default aggregating sum has two typed inputs and one typed ``value`` output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_SUM_8BIT, filter_id="s"
        )
        self.assertEqual(f.filter_configurations["input_count"], "2")
        self.assertEqual(f.in_data_types, {"0": DataType.DT_8_BIT, "1": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_8_BIT})
        self.assertEqual(f.default_values, {"0": "0", "1": "0"})

    def test_data_type_per_subclass(self) -> None:
        """Each aggregating subclass applies its data type to inputs, output, and defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_SUM_8BIT, DataType.DT_8_BIT, "0"),
            (FilterTypeEnumeration.FILTER_SUM_16BIT, DataType.DT_16_BIT, "0"),
            (FilterTypeEnumeration.FILTER_SUM_FLOAT, DataType.DT_DOUBLE, "0.0"),
            (FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV, DataType.DT_COLOR, "0,0,0"),
            (FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB, DataType.DT_COLOR, "0,0,0"),
            (FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATIVE_RGB, DataType.DT_COLOR, "0,0,0"),
        ]
        for ft, expected_dt, expected_default in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"a_{ft.name}")
                self.assertEqual(f.in_data_types["0"], expected_dt)
                self.assertEqual(f.out_data_types["value"], expected_dt)
                self.assertEqual(f.default_values["0"], expected_default)

    def test_input_count_three_populates_three_inputs(self) -> None:
        """``input_count=3`` on the aggregating color mixer exposes three typed inputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV,
            filter_id="m",
            filter_configurations={"input_count": "3"},
        )
        self.assertEqual(set(f.in_data_types.keys()), {"0", "1", "2"})
        for key in ("0", "1", "2"):
            self.assertEqual(f.in_data_types[key], DataType.DT_COLOR)
            self.assertEqual(f.default_values[key], "0,0,0")

    def test_invalid_input_count_falls_back_to_zero(self) -> None:
        """A non-numeric ``input_count`` config degrades to zero inputs."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SUM_FLOAT,
            filter_id="s",
            filter_configurations={"input_count": "garbage"},
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.filter_configurations["input_count"], "0")

    def test_changing_input_count_syncs_pyqtgraph_terminals(self) -> None:
        """Dynamic rebuild: shrink from 3 inputs to 1 via update_node_after_settings_changed."""
        from view.show_mode.editor.nodes.impl.arithmetics import Sum8BitNode

        scene = self._make_scene()
        node = Sum8BitNode(model=scene, name="s")
        node.filter.filter_configurations["input_count"] = "3"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"0", "1", "2"})
        node.filter.filter_configurations["input_count"] = "1"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"0"})
        self.assertEqual(set(node.outputs().keys()), {"value"})
