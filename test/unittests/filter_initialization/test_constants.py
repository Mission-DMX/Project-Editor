"""Per-type assertions for constant filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ConstantSubclassTests(unittest.TestCase):
    """Per-type assertions for the native constant subclasses migrated in PR 2.

    Covers both the regular constants and their ``RESPONDING_*`` siblings, which share the
    same class under multiple registered type codes.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_constant_8bit_signature(self) -> None:
        """Constant 8bit exposes a single DT_8_BIT ``value`` output with gui-update binding."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT, filter_id="c"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_8_BIT})
        self.assertEqual(f.initial_parameters["value"], "0")
        self.assertEqual(f.gui_update_keys["value"], DataType.DT_8_BIT)
        self.assertTrue(f.configuration_supported)

    def test_constant_16bit_signature(self) -> None:
        """Constant 16bit exposes a single DT_16_BIT ``value`` output with ``0`` default."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, filter_id="c"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f.initial_parameters["value"], "0")

    def test_constant_float_signature(self) -> None:
        """Constant float exposes a single DT_DOUBLE ``value`` output with ``0.0`` default."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, filter_id="c"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.initial_parameters["value"], "0.0")

    def test_constant_color_signature(self) -> None:
        """Constant color exposes a single DT_COLOR ``value`` output with ``0,0,0`` default."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR, filter_id="c"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(f.initial_parameters["value"], "0,0,0")

    def test_responding_constants_share_subclass_but_keep_their_type_code(self) -> None:
        """A responding-constant filter uses the same subclass but keeps its own filter_type."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.constants import Constant8Bit
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        regular = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT, filter_id="c"
        )
        responding = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT, filter_id="r"
        )
        self.assertIsInstance(regular, Constant8Bit)
        self.assertIsInstance(responding, Constant8Bit)
        # Filter type codes stay distinct — that's what fish uses to pick the right C++ class
        self.assertEqual(int(regular.filter_type), int(FilterTypeEnumeration.FILTER_CONSTANT_8BIT))
        self.assertEqual(int(responding.filter_type), int(FilterTypeEnumeration.FILTER_RESPONDING_CONSTANT_8BIT))
        # Both get the same I/O signature
        self.assertEqual(regular.out_data_types, {"value": DataType.DT_8_BIT})
        self.assertEqual(responding.out_data_types, {"value": DataType.DT_8_BIT})

    def test_constant_color_node_reads_default_after_slimdown(self) -> None:
        """ConstantsColorNode reads filter.initial_parameters['value'] to build its colour brush.

        After PR 2 the node no longer sets the default itself; the subclass's
        ``DEFAULT_INITIAL_PARAMETERS`` must supply it so the brush construction succeeds.
        """
        from view.show_mode.editor.nodes.impl.constants import ConstantsColorNode

        scene = self._make_scene()
        node = ConstantsColorNode(model=scene, name="col")
        self.assertEqual(node.filter.initial_parameters["value"], "0,0,0")
        self.assertIsNotNone(node._color_brush)
