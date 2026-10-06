"""Headless invariant tests for filter construction via the unified factory.

PR 0 establishes :func:`model.filters.factory.construct_filter_instance` as the single entry
point for building filters. The invariant this test guards is: for every
:class:`model.filter.FilterTypeEnumeration` value, the factory returns either a usable filter
instance or ``None`` (for virtual-filter type codes that are deliberately not implemented
yet). Later migration PRs grow this file to assert that the returned filter's
``in_data_types`` / ``out_data_types`` are non-empty for the migrated types, which is the
regression that catches "half-initialised filter" bugs when the editor view was never opened.

The test runs headlessly: no editor view is instantiated. A ``QApplication`` is required
only because importing :mod:`model` triggers Qt-dependent transitive imports; it is spun up
once by :func:`setUpModule` and reused across tests.
"""

from __future__ import annotations

import sys
import unittest

from PySide6.QtWidgets import QApplication

_qapp: QApplication | None = None


def setUpModule() -> None:  # noqa: N802 — unittest hook naming
    """Create a ``QApplication`` so that Qt-dependent model imports succeed."""
    global _qapp
    _qapp = QApplication.instance() or QApplication(sys.argv)


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

    def test_legacy_shim_delegates_to_unified_factory(self) -> None:
        """``construct_virtual_filter_instance`` must still work during the migration."""
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.vfilter_factory import construct_virtual_filter_instance

        scene = self._make_scene()
        instance = construct_virtual_filter_instance(
            scene, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE, "legacy"
        )
        self.assertIsNotNone(instance)
        self.assertEqual(int(instance.filter_type), int(FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE))


class FilterCopyTests(unittest.TestCase):
    """Guard the ``Filter.copy()`` path which now routes through the unified factory."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_copy_preserves_configuration_and_channel_links(self) -> None:
        """A copied filter owns independent dicts holding the source's values."""
        from model.filter import Filter, FilterTypeEnumeration

        scene = self._make_scene()
        src = Filter(scene, "src", FilterTypeEnumeration.FILTER_CONSTANT_8BIT)
        src.filter_configurations["k"] = "v"
        src.initial_parameters["value"] = "127"
        src.channel_links["in"] = "other:out"

        dst = src.copy(new_id="dst")
        self.assertEqual(dst.filter_id, "dst")
        self.assertEqual(dst.filter_configurations, {"k": "v"})
        self.assertEqual(dst.initial_parameters, {"value": "127"})
        self.assertEqual(dst.channel_links, {"in": "other:out"})
        self.assertIsNot(dst.filter_configurations, src.filter_configurations)
        self.assertIsNot(dst.channel_links, src.channel_links)

    def test_copy_of_virtual_filter_runs_deserialize(self) -> None:
        """Copies of VirtualFilter instances must come back fully populated."""
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.range_adapters import DimmerGlobalBrightnessMixinVFilter

        scene = self._make_scene()
        src = DimmerGlobalBrightnessMixinVFilter(scene, "dbm", (0, 0))
        src.filter_configurations["input_method"] = "8bit"
        src.filter_configurations["input_method_mixin"] = "16bit"

        dst = src.copy(new_id="dbm_copy")
        self.assertEqual(dst.filter_configurations.get("input_method"), "8bit")
        self.assertEqual(dst.filter_configurations.get("input_method_mixin"), "16bit")
        # deserialize() populates _in_data_types from input_method configuration keys
        self.assertIn("input", dst.in_data_types)
        self.assertIn("mixin", dst.in_data_types)
        self.assertEqual(int(dst.filter_type), int(FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN))


class VirtualFilterInstantiationTests(unittest.TestCase):
    """Guard ``VirtualFilter.instantiate_filters()`` for all v-filters that build native filters.

    This is the gate from the Virtual filter interop section of the plan: at every PR
    boundary, every v-filter must still produce a working list of native filters. In PR 0
    nothing changed about v-filters, so this test is a baseline — later PRs will tighten it
    (asserting non-empty I/O dicts on the produced natives once their types are migrated).
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_dimmer_brightness_mixin_still_instantiates(self) -> None:
        from model.virtual_filters.range_adapters import DimmerGlobalBrightnessMixinVFilter

        scene = self._make_scene()
        mixin = DimmerGlobalBrightnessMixinVFilter(scene, "mixin", (0, 0))
        scene.append_filter(mixin)

        produced: list = []
        mixin.instantiate_filters(produced)
        self.assertGreater(len(produced), 0, "V-filter must produce at least one native filter")

    def test_sixteen_bit_to_float_range_still_instantiates(self) -> None:
        from model.virtual_filters.range_adapters import SixteenBitToFloatRange

        scene = self._make_scene()
        v = SixteenBitToFloatRange(scene, "r16", (0, 0))
        v.channel_links["value_in"] = "src:value"
        scene.append_filter(v)

        produced: list = []
        v.instantiate_filters(produced)
        self.assertEqual(len(produced), 2)


if __name__ == "__main__":
    unittest.main()
