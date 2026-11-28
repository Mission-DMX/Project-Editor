"""Per-type assertions for switch filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class SwitchSubclassTests(unittest.TestCase):
    """Per-type assertions for the native switch subclasses migrated in PR 11.

    Also confirms the latent bug fix: ``out_data_types["out"]`` is now set (previously the
    typed output was mistakenly stored under ``in_data_types["out"]``).
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_two_inputs_plus_select(self) -> None:
        """Default switch has two typed inputs plus a 16-bit ``select`` input and typed ``out``."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_SWITCH_8BIT, filter_id="sw"
        )
        self.assertEqual(f.filter_configurations["nr_inputs"], "2")
        self.assertEqual(
            f.in_data_types,
            {"select": DataType.DT_16_BIT, "0": DataType.DT_8_BIT, "1": DataType.DT_8_BIT},
        )
        self.assertEqual(f.out_data_types, {"out": DataType.DT_8_BIT})
        self.assertEqual(f.default_values["select"], "0")
        self.assertEqual(f.default_values["0"], "0")

    def test_data_type_per_subclass_and_defaults(self) -> None:
        """Each switch subclass uses its specific data type for inputs, output, and defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_SWITCH_8BIT, DataType.DT_8_BIT, "0"),
            (FilterTypeEnumeration.FILTER_SWITCH_16BIT, DataType.DT_16_BIT, "0"),
            (FilterTypeEnumeration.FILTER_SWITCH_FLOAT, DataType.DT_DOUBLE, "0"),
            (FilterTypeEnumeration.FILTER_SWITCH_COLOR, DataType.DT_COLOR, "0,0,0"),
        ]
        for ft, expected_dt, expected_default in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"s_{ft.name}")
                self.assertEqual(f.in_data_types["0"], expected_dt)
                self.assertEqual(f.in_data_types["select"], DataType.DT_16_BIT)
                self.assertEqual(f.out_data_types, {"out": expected_dt})
                self.assertEqual(f.default_values["0"], expected_default)

    def test_output_is_in_out_data_types_not_in_data_types(self) -> None:
        """Guard against the pre-PR 11 bug that stored the output type under in_data_types."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_SWITCH_FLOAT, filter_id="s"
        )
        self.assertNotIn("out", f.in_data_types)
        self.assertIn("out", f.out_data_types)

    def test_nr_inputs_three_grows_input_set(self) -> None:
        """Setting ``nr_inputs=3`` adds three numbered typed inputs alongside ``select``."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SWITCH_COLOR,
            filter_id="s",
            filter_configurations={"nr_inputs": "3"},
        )
        self.assertEqual(set(f.in_data_types.keys()), {"select", "0", "1", "2"})
        for key in ("0", "1", "2"):
            self.assertEqual(f.in_data_types[key], DataType.DT_COLOR)
            self.assertEqual(f.default_values[key], "0,0,0")

    def test_invalid_nr_inputs_falls_back_to_zero(self) -> None:
        """A non-numeric ``nr_inputs`` config leaves only the ``select`` input in place."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SWITCH_8BIT,
            filter_id="s",
            filter_configurations={"nr_inputs": "garbage"},
        )
        # Only the select input remains.
        self.assertEqual(set(f.in_data_types.keys()), {"select"})
        self.assertEqual(f.in_data_types["select"], DataType.DT_16_BIT)
        self.assertEqual(f.filter_configurations["nr_inputs"], "0")

    def test_switch_node_syncs_terminals_on_settings_change(self) -> None:
        """Dynamic rebuild: 2 inputs → 4 inputs → 1 input via base update_node_after_settings_changed."""
        from view.show_mode.editor.nodes.impl.routing import Switch8BitNode

        scene = self._make_scene()
        node = Switch8BitNode(model=scene, name="sw")
        self.assertEqual(set(node.inputs().keys()), {"select", "0", "1"})
        self.assertEqual(set(node.outputs().keys()), {"out"})
        node.filter.filter_configurations["nr_inputs"] = "4"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"select", "0", "1", "2", "3"})
        node.filter.filter_configurations["nr_inputs"] = "1"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"select", "0"})
        self.assertEqual(set(node.outputs().keys()), {"out"})
