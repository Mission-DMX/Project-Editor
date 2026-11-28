"""Per-type assertions for shift filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ShiftSubclassTests(unittest.TestCase):
    """Per-type assertions for the native shift-effect subclasses migrated in PR 15."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_and_defaults(self) -> None:
        """Default shift filter exposes input/time inputs and zero outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT, filter_id="sh"
        )
        self.assertEqual(
            f.in_data_types,
            {"input": DataType.DT_8_BIT, "switch_time": DataType.DT_DOUBLE, "time": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.default_values["switch_time"], "1000")
        self.assertEqual(f.default_values["time"], "0")
        self.assertEqual(f.filter_configurations["nr_outputs"], "0")

    def test_data_type_per_subclass(self) -> None:
        """Each shift subclass carries its own data type on the ``input`` terminal."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT, DataType.DT_8_BIT),
            (FilterTypeEnumeration.FILTER_EFFECT_SHIFT_16BIT, DataType.DT_16_BIT),
            (FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT, DataType.DT_DOUBLE),
            (FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR, DataType.DT_COLOR),
        ]
        for ft, expected_dt in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"s_{ft.name}")
                self.assertEqual(f.in_data_types["input"], expected_dt)
                self.assertEqual(int(f.filter_type), int(ft))

    def test_nr_outputs_populates_output_set(self) -> None:
        """``nr_outputs=N`` populates N typed ``output_i`` ports on the shift subclass."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR,
            filter_id="s",
            filter_configurations={"nr_outputs": "3"},
        )
        self.assertEqual(set(f.out_data_types.keys()), {"output_1", "output_2", "output_3"})
        for key in ("output_1", "output_2", "output_3"):
            self.assertEqual(f.out_data_types[key], DataType.DT_COLOR)

    def test_invalid_nr_outputs_falls_back_to_zero(self) -> None:
        """A non-numeric ``nr_outputs`` config results in zero outputs."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT,
            filter_id="s",
            filter_configurations={"nr_outputs": "garbage"},
        )
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.filter_configurations["nr_outputs"], "0")

    def test_shift_node_syncs_terminals_on_settings_change(self) -> None:
        """Dynamic rebuild: 0 outputs → 2 outputs → 1 output via update_node_after_settings_changed."""
        from view.show_mode.editor.nodes.impl.effects import Shift16BitNode

        scene = self._make_scene()
        node = Shift16BitNode(model=scene, name="sh")
        self.assertEqual(set(node.outputs().keys()), set())
        node.filter.filter_configurations["nr_outputs"] = "2"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.outputs().keys()), {"output_1", "output_2"})
        node.filter.filter_configurations["nr_outputs"] = "1"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.outputs().keys()), {"output_1"})
