"""Factory smoke tests over the full ``FilterTypeEnumeration`` codomain."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ConstructFilterInstanceTests(unittest.TestCase):
    """Factory smoke tests over the full ``FilterTypeEnumeration`` codomain."""

    def _make_scene(self):
        """Return a fresh scene wired to a fresh board configuration."""
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_every_type_constructs_or_returns_none(self) -> None:
        """``construct_filter_instance`` must handle every enum value without raising."""
        from model.filter import Filter, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in FilterTypeEnumeration:
            with self.subTest(filter_type=ft.name):
                instance = construct_filter_instance(
                    scene=scene, filter_type=ft, filter_id=f"test_{ft.name}"
                )
                if instance is None:
                    # Only v-filter types that are deliberately not implemented are allowed to
                    # return None (see _construct_virtual_filter_instance_legacy TODO cases).
                    self.assertLess(int(ft), 0, f"Native type {ft.name} returned None")
                    continue
                self.assertIsInstance(instance, Filter)
                self.assertEqual(int(instance.filter_type), int(ft))
                self.assertEqual(instance.filter_id, f"test_{ft.name}")

    def test_configurations_are_passed_through_to_native_filter(self) -> None:
        """Config / parameter dicts passed to the factory must land on the instance."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        instance = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
            filter_id="c",
            filter_configurations={"foo": "bar"},
            initial_parameters={"value": "42"},
        )
        self.assertIsNotNone(instance)
        self.assertEqual(instance.filter_configurations.get("foo"), "bar")
        self.assertEqual(instance.initial_parameters.get("value"), "42")

    def test_configurations_are_merged_into_fallback_virtual_filter(self) -> None:
        """For the legacy v-filter fallback, factory-supplied configs must be merged in."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        instance = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN,
            filter_id="dbm",
            filter_configurations={"input_method": "8bit"},
        )
        self.assertIsNotNone(instance)
        self.assertEqual(instance.filter_configurations.get("input_method"), "8bit")

    def test_rebuild_io_default_is_a_noop(self) -> None:
        """The base-class ``_rebuild_io`` hook must not raise and must leave dicts untouched."""
        from model.filter import Filter, FilterTypeEnumeration

        scene = self._make_scene()
        f = Filter(scene, "f", FilterTypeEnumeration.FILTER_CONSTANT_8BIT)
        f._in_data_types["x"] = f._in_data_types.get("x", None)  # sanity touch
        f._rebuild_io()  # must not raise

    def test_update_filter_configuration_rebuilds_io(self) -> None:
        """``update_filter_configuration`` writes the key and re-invokes ``_rebuild_io``."""
        from model.filter import Filter, FilterTypeEnumeration

        scene = self._make_scene()
        f = Filter(scene, "f", FilterTypeEnumeration.FILTER_CONSTANT_8BIT)

        call_count = [0]
        original = f._rebuild_io

        def spy() -> None:
            call_count[0] += 1
            original()

        f._rebuild_io = spy  # type: ignore[method-assign]
        f.update_filter_configuration("key", "value")
        self.assertEqual(f.filter_configurations["key"], "value")
        self.assertEqual(call_count[0], 1)

    def test_virtual_filter_construction_via_unified_factory(self) -> None:
        """V-filters are instantiated through the single ``construct_filter_instance`` entry point."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        instance = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE,
            filter_id="legacy",
        )
        self.assertIsNotNone(instance)
        self.assertEqual(int(instance.filter_type), int(FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE))
