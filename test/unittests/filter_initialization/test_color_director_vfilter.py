"""Tests for the ColorDirector virtual filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ColorDirectorVFilterTests(unittest.TestCase):
    """Per-type assertions for ColordirectorVFilter migrated in PR 21."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_without_color_groups(self) -> None:
        """A fresh ColordirectorVFilter exposes only time inputs and no outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_COLORDIRECTOR, filter_id="cd"
        )
        self.assertEqual(
            f.in_data_types,
            {"time": DataType.DT_DOUBLE, "time_scale": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {})

    def test_color_group_mutations_sync_to_rebuild_io(self) -> None:
        """``_rebuild_io`` derives one DT_COLOR output per color-group sub-output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_COLORDIRECTOR, filter_id="cd"
        )
        # UI mutators only touch the model fields; _rebuild_io is the derivation point.
        f.add_output_group("stage")
        f.add_sub_output("stage", "left")
        f.add_sub_output("stage", "right")
        f.add_output_group("backdrop")
        f.add_sub_output("backdrop", "top")
        f._rebuild_io()
        self.assertEqual(
            set(f.out_data_types.keys()),
            {"stage__left", "stage__right", "backdrop__top"},
        )
        for value in f.out_data_types.values():
            self.assertEqual(value, DataType.DT_COLOR)

    def test_deserialize_populates_outputs_from_filter_configurations(self) -> None:
        """Loader-equivalent path: configs → ``deserialize`` → ``_rebuild_io`` → outputs."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        # Match the on-disk serialization format: ``#``-separated groups whose fields
        # (name + channels) are ``|``-separated.
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_COLORDIRECTOR,
            filter_id="cd",
            filter_configurations={"colorgroups": "stage|left|right#backdrop|top", "format_version": "1"},
        )
        # Loader equivalent: after XML populates filter_configurations, deserialize() parses
        # them into the rich _color_groups / _presets / _recalls state and triggers _rebuild_io.
        f.deserialize()
        self.assertEqual(
            set(f.out_data_types.keys()),
            {"stage__left", "stage__right", "backdrop__top"},
        )
        self.assertEqual(f.out_data_types["stage__left"], DataType.DT_COLOR)

    def test_group_removal_shrinks_outputs_on_rebuild(self) -> None:
        """Removing sub-outputs and groups must drop the corresponding outputs after rebuild."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_COLORDIRECTOR, filter_id="cd"
        )
        f.add_output_group("stage")
        f.add_sub_output("stage", "left")
        f.add_sub_output("stage", "right")
        f._rebuild_io()
        self.assertIn("stage__left", f.out_data_types)
        f.remove_sub_output("stage", "left")
        f._rebuild_io()
        self.assertNotIn("stage__left", f.out_data_types)
        self.assertIn("stage__right", f.out_data_types)
        f.remove_output_group("stage")
        f._rebuild_io()
        self.assertEqual(f.out_data_types, {})
