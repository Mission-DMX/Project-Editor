"""Per-type assertions for trigonometric filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class TrigonometricSubclassTests(unittest.TestCase):
    """Per-type assertions for the native trig subclasses migrated in PR 5."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_forward_trig_shared_signature_and_defaults(self) -> None:
        """Sin/cos/tan subclasses share the five-input signature and defaults."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        expected_in = {
            "value_in": DataType.DT_DOUBLE,
            "factor_outer": DataType.DT_DOUBLE,
            "factor_inner": DataType.DT_DOUBLE,
            "phase": DataType.DT_DOUBLE,
            "offset": DataType.DT_DOUBLE,
        }
        expected_defaults = {
            "factor_outer": "1",
            "factor_inner": "0.1",
            "phase": "0",
            "offset": "0",
        }
        for ft in (
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN,
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN,
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_TANGENT,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"t_{ft.name}")
                self.assertEqual(f.in_data_types, expected_in)
                self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
                self.assertEqual(f.default_values, expected_defaults)
                self.assertFalse(f.configuration_supported)

    def test_arc_trig_adds_value_in_default(self) -> None:
        """Arc-trig filters seed a non-zero ``value_in`` default."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in (
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCSIN,
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCCOSIN,
            FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCTANGENT,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"t_{ft.name}")
                self.assertEqual(f.default_values["value_in"], "1")
                self.assertEqual(f.default_values["factor_outer"], "1")

    def test_trig_node_still_sets_channel_hints(self) -> None:
        """UI-only channel hints must still be attached by the node after slim-down."""
        from view.show_mode.editor.nodes.impl.trigonometics import TrigonometricSineNode

        scene = self._make_scene()
        node = TrigonometricSineNode(model=scene, name="sin")
        self.assertEqual(node.channel_hints["phase"], " [deg]")
        self.assertEqual(node.channel_hints["value_in"], " [deg]")
