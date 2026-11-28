"""Tests for the import virtual filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ImportVFilterTests(unittest.TestCase):
    """Per-type assertions for ImportVFilter migrated in PR 20."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_without_target(self) -> None:
        """A targetless ImportVFilter exposes no I/O and empty target/rename configs."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_IMPORT, filter_id="imp"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.filter_configurations["target"], "")
        self.assertEqual(f.filter_configurations["rename_dict"], "")

    def test_mirrors_target_outputs(self) -> None:
        """ImportVFilter mirrors the output signature of its ``target`` filter."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        source = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT, filter_id="src"
        )
        scene.append_filter(source)
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_IMPORT,
            filter_id="imp",
            filter_configurations={"target": "src"},
        )
        # Constant 8bit exposes {"value": DT_8_BIT}; the import mirrors it.
        self.assertEqual(f.out_data_types, {"value": DataType.DT_8_BIT})

    def test_rename_dict_renames_and_hides_outputs(self) -> None:
        """A ``rename_dict`` config must rename, drop, or keep imported outputs as specified."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        source = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB, filter_id="src"
        )
        scene.append_filter(source)
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_IMPORT,
            filter_id="imp",
            filter_configurations={"target": "src", "rename_dict": "r=red,b="},
        )
        # "r" renamed to "red"; "b" hidden; "g" kept as-is.
        self.assertEqual(set(f.out_data_types.keys()), {"red", "g"})
        self.assertEqual(f.out_data_types["red"], DataType.DT_8_BIT)
        self.assertEqual(f.out_data_types["g"], DataType.DT_8_BIT)
