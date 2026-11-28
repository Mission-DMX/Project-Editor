"""Per-type assertions for wave generator filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class WaveSubclassTests(unittest.TestCase):
    """Per-type assertions for the native wave-generator subclasses migrated in PR 6."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_triangle_and_sawtooth_share_trig_signature(self) -> None:
        """Triangle and sawtooth waves share the five-input trig signature with one double output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in (
            FilterTypeEnumeration.FILTER_WAVES_TRIANGLE,
            FilterTypeEnumeration.FILTER_WAVES_SAWTOOTH,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"w_{ft.name}")
                self.assertEqual(set(f.in_data_types.keys()), {"value_in", "factor_outer", "factor_inner", "phase", "offset"})
                self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
                self.assertFalse(f.configuration_supported)

    def test_square_adds_length_input_with_default(self) -> None:
        """Square wave adds a ``length`` input with a 180 default on top of the trig signature."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_WAVES_SQUARE, filter_id="sq"
        )
        # Trig base inputs still present
        for key in ("value_in", "factor_outer", "factor_inner", "phase", "offset"):
            self.assertIn(key, f.in_data_types)
        # Extra square-specific input
        self.assertEqual(f.in_data_types["length"], DataType.DT_DOUBLE)
        self.assertEqual(f.default_values["length"], "180")
        # Base trig defaults carried over
        self.assertEqual(f.default_values["factor_outer"], "1")

    def test_square_node_has_length_terminal_without_explicit_add(self) -> None:
        """After migration the node no longer calls addInput('length'); the base derives it."""
        from view.show_mode.editor.nodes.impl.waves import SquareWaveNode

        scene = self._make_scene()
        node = SquareWaveNode(model=scene, name="sq")
        self.assertIn("length", node.inputs())
