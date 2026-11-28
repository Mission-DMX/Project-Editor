"""Per-type assertions for debug output filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class DebugSubclassTests(unittest.TestCase):
    """Per-type assertions for the native debug subclasses migrated in PR 3.

    Local (``FILTER_DEBUG_OUTPUT_*``) and remote (``FILTER_REMOTE_DEBUG_*``) codes share
    classes but keep their distinct ``filter_type`` codes.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_all_debug_types_have_single_value_input_and_no_output(self) -> None:
        """Every debug subclass exposes a single typed ``value`` input and no outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        cases = [
            (FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_8BIT, DataType.DT_8_BIT),
            (FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT, DataType.DT_8_BIT),
            (FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_16BIT, DataType.DT_16_BIT),
            (FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT, DataType.DT_16_BIT),
            (FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_FLOAT, DataType.DT_DOUBLE),
            (FilterTypeEnumeration.FILTER_REMOTE_DEBUG_FLOAT, DataType.DT_DOUBLE),
            (FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_COLOR, DataType.DT_COLOR),
            (FilterTypeEnumeration.FILTER_REMOTE_DEBUG_PIXEL, DataType.DT_COLOR),
        ]
        scene = self._make_scene()
        for ft, expected_dt in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"d_{ft.name}")
                self.assertEqual(f.in_data_types, {"value": expected_dt})
                self.assertEqual(f.out_data_types, {})
                self.assertFalse(f.configuration_supported)
                self.assertEqual(int(f.filter_type), int(ft))

    def test_debug_local_and_remote_share_class(self) -> None:
        """Local and remote 8-bit debug filters both resolve to the ``Debug8Bit`` class."""
        from model.filter import FilterTypeEnumeration
        from model.filters.debug import Debug8Bit
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        local = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_DEBUG_OUTPUT_8BIT, filter_id="l"
        )
        remote = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT, filter_id="r"
        )
        self.assertIsInstance(local, Debug8Bit)
        self.assertIsInstance(remote, Debug8Bit)
