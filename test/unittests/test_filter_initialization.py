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

import gc
import sys
import unittest

from PySide6.QtWidgets import QApplication

_qapp: QApplication | None = None


def setUpModule() -> None:  # noqa: N802 — unittest hook naming
    """Create a ``QApplication`` and silence cyclic GC for the test module.

    Several tests instantiate pyqtgraph ``Node`` / ``Terminal`` graphics objects wrapped
    around freshly-made ``Scene`` instances. Those pyqtgraph objects hold shiboken-managed
    ``QGraphicsItem`` handles that outlive the Python-side ``Scene`` references, so a
    cyclic-GC pass fired during an unrelated test's ``itemChange`` callback can traverse a
    dangling C++ pointer and segfault the whole process. Disabling the cyclic collector
    while the module runs keeps object teardown deterministic; the ``tearDownModule`` hook
    re-enables it afterwards.
    """
    global _qapp
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 — unittest hook naming
    """Re-enable the cyclic garbage collector that ``setUpModule`` turned off."""
    gc.enable()


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


class AdapterSubclassTests(unittest.TestCase):
    """Per-type assertions for the native adapter subclasses migrated in PR 1.

    Each subclass must initialise its I/O signature at construction time, without the
    corresponding node ever being created. Any new migration adds assertions here.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_adapter_16bit_to_dual_8bit_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value_lower": DataType.DT_8_BIT, "value_upper": DataType.DT_8_BIT})
        self.assertFalse(f.configuration_supported)

    def test_adapter_16bit_to_bool_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_BOOL, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_BOOL})
        self.assertFalse(f.configuration_supported)

    def test_adapter_16bit_to_float_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_16_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})

    def test_adapter_8bit_to_float_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})

    def test_adapter_color_to_rgb_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(
            f.out_data_types,
            {"r": DataType.DT_8_BIT, "g": DataType.DT_8_BIT, "b": DataType.DT_8_BIT},
        )

    def test_adapter_color_to_rgbw_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW, filter_id="a"
        )
        self.assertEqual(set(f.out_data_types.keys()), {"r", "g", "b", "w"})

    def test_adapter_color_to_rgbwa_signature(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBWA, filter_id="a"
        )
        self.assertEqual(set(f.out_data_types.keys()), {"r", "g", "b", "w", "a"})

    def test_adapter_float_to_color_signature_and_default_value(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR, filter_id="a"
        )
        self.assertEqual(
            f.in_data_types,
            {"h": DataType.DT_DOUBLE, "s": DataType.DT_DOUBLE, "i": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(f.default_values, {"i": "1"})

    def test_adapter_color_to_float_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"input": DataType.DT_COLOR})
        self.assertEqual(set(f.out_data_types.keys()), {"h", "s", "i"})

    def test_dual_byte_to_16bit_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_DUAL_BYTE_TO_16BIT, filter_id="a"
        )
        self.assertEqual(set(f.in_data_types.keys()), {"lower", "upper"})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})

    def test_8bit_to_16bit_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_8BIT_TO_16BIT, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})

    def test_float_to_float_range_signature_and_defaults(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE, filter_id="a"
        )
        self.assertEqual(f.in_data_types, {"value_in": DataType.DT_DOUBLE})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.initial_parameters["lower_bound_in"], "0")
        self.assertEqual(f.initial_parameters["upper_bound_in"], "1")
        self.assertEqual(f.initial_parameters["lower_bound_out"], "0")
        self.assertEqual(f.initial_parameters["upper_bound_out"], "1")
        self.assertEqual(f.initial_parameters["limit_range"], "0")
        self.assertIn("lower_bound_in", f.gui_update_keys)
        self.assertIn("limit_range", f.gui_update_keys)
        self.assertTrue(f.configuration_supported)  # range adapters allow user config

    def test_float_to_8bit_range_defaults(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE, filter_id="a"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_8_BIT})
        self.assertEqual(f.initial_parameters["upper_bound_out"], "255")

    def test_float_to_16bit_range_defaults(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE, filter_id="a"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f.initial_parameters["upper_bound_out"], "65535")

    def test_loader_initial_parameters_override_subclass_defaults(self) -> None:
        """Loaded ``initial_parameters`` must take precedence over subclass defaults."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE,
            filter_id="a",
            initial_parameters={"upper_bound_out": "100", "custom_future_key": "x"},
        )
        # loaded value wins
        self.assertEqual(f.initial_parameters["upper_bound_out"], "100")
        # unknown-but-loaded keys are preserved on round-trip
        self.assertEqual(f.initial_parameters["custom_future_key"], "x")
        # other defaults still applied
        self.assertEqual(f.initial_parameters["lower_bound_in"], "0")


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
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, filter_id="c"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f.initial_parameters["value"], "0")

    def test_constant_float_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, filter_id="c"
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.initial_parameters["value"], "0.0")

    def test_constant_color_signature(self) -> None:
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


class ArithmeticSubclassTests(unittest.TestCase):
    """Per-type assertions for the native arithmetic subclasses migrated in PR 4.

    Covers the static-I/O arithmetics only. The ``FILTER_SUM_*`` aggregating filters have
    configuration-dependent input counts and will be covered when the aggregating category
    migrates.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_mac_signature_and_defaults(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC, filter_id="m")
        self.assertEqual(
            f.in_data_types,
            {"factor1": DataType.DT_DOUBLE, "factor2": DataType.DT_DOUBLE, "summand": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertEqual(f.default_values, {"factor1": "1.0", "factor2": "1.0", "summand": "0.0"})
        self.assertFalse(f.configuration_supported)

    def test_float_to_byte_converters(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f16 = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_16BIT, filter_id="f16"
        )
        f8 = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT, filter_id="f8"
        )
        self.assertEqual(f16.in_data_types, {"value_in": DataType.DT_DOUBLE})
        self.assertEqual(f16.out_data_types, {"value": DataType.DT_16_BIT})
        self.assertEqual(f8.out_data_types, {"value": DataType.DT_8_BIT})

    def test_round_log_exp_signatures(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in (
            FilterTypeEnumeration.FILTER_ARITHMETICS_ROUND,
            FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM,
            FilterTypeEnumeration.FILTER_ARITHMETICS_EXPONENTIAL,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"a_{ft.name}")
                self.assertEqual(f.in_data_types, {"value_in": DataType.DT_DOUBLE})
                self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        # log has a non-zero default input value to keep ln(0) at bay
        log_f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_LOGARITHM, filter_id="l"
        )
        self.assertEqual(log_f.default_values["value_in"], "1")

    def test_min_max_signatures_and_defaults(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        for ft in (
            FilterTypeEnumeration.FILTER_ARITHMETICS_MINIMUM,
            FilterTypeEnumeration.FILTER_ARITHMETICS_MAXIMUM,
        ):
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"a_{ft.name}")
                self.assertEqual(
                    f.in_data_types, {"param1": DataType.DT_DOUBLE, "param2": DataType.DT_DOUBLE}
                )
                self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
                self.assertEqual(f.default_values, {"param1": "1", "param2": "1"})


class TrigonometricSubclassTests(unittest.TestCase):
    """Per-type assertions for the native trig subclasses migrated in PR 5."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_forward_trig_shared_signature_and_defaults(self) -> None:
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


class WaveSubclassTests(unittest.TestCase):
    """Per-type assertions for the native wave-generator subclasses migrated in PR 6."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_triangle_and_sawtooth_share_trig_signature(self) -> None:
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


class TimeSubclassTests(unittest.TestCase):
    """Per-type assertions for the native time-filter subclasses migrated in PR 7."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_time_input_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT, filter_id="t"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_DOUBLE})
        self.assertFalse(f.configuration_supported)

    def test_event_counter_signature_and_default_event_configuration(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_EVENT_COUNTER, filter_id="c"
        )
        self.assertEqual(f.in_data_types, {"time": DataType.DT_DOUBLE})
        self.assertEqual(f.out_data_types, {"bpm": DataType.DT_16_BIT, "freq": DataType.DT_16_BIT})
        self.assertEqual(f.filter_configurations["event"], "0:0")
        self.assertTrue(f.configuration_supported)

    def test_switch_delay_shared_signature_per_data_type(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_8BIT, DataType.DT_8_BIT),
            (FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_8BIT, DataType.DT_8_BIT),
            (FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_16BIT, DataType.DT_16_BIT),
            (FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_16BIT, DataType.DT_16_BIT),
            (FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_FLOAT, DataType.DT_DOUBLE),
            (FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_FLOAT, DataType.DT_DOUBLE),
        ]
        for ft, expected_dt in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"d_{ft.name}")
                self.assertEqual(f.in_data_types["value_in"], expected_dt)
                self.assertEqual(f.in_data_types["time"], DataType.DT_DOUBLE)
                self.assertEqual(f.out_data_types, {"value": expected_dt})
                self.assertEqual(f.filter_configurations["delay"], "0.0")
                self.assertEqual(int(f.filter_type), int(ft))

    def test_switch_delay_on_and_off_share_class_per_data_type(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance
        from model.filters.time import TimeDelay8Bit

        scene = self._make_scene()
        on_f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_8BIT, filter_id="on"
        )
        off_f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_OFF_DELAY_8BIT, filter_id="off"
        )
        self.assertIsInstance(on_f, TimeDelay8Bit)
        self.assertIsInstance(off_f, TimeDelay8Bit)

    def test_delay_configuration_is_preserved_when_loaded(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_TIME_SWITCH_ON_DELAY_FLOAT,
            filter_id="d",
            filter_configurations={"delay": "2.5", "future_key": "x"},
        )
        self.assertEqual(f.filter_configurations["delay"], "2.5")
        self.assertEqual(f.filter_configurations["future_key"], "x")


class LuaScriptingTests(unittest.TestCase):
    """Per-type assertions for the Lua scripting subclass migrated in PR 8.

    Also covers the base ``update_node_after_settings_changed`` promotion: the Lua filter is
    the first dynamic-I/O subclass in the hierarchy, so its node relies on the base's
    generic rebuild+sync behaviour instead of a custom override.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_mappings_and_script_applied(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA, filter_id="lua")
        self.assertEqual(f.filter_configurations["in_mapping"], "")
        self.assertEqual(f.filter_configurations["out_mapping"], "")
        self.assertIn("function update()", f.initial_parameters["script"])
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})

    def test_mapping_parsing_populates_io(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA,
            filter_id="lua",
            filter_configurations={"in_mapping": "a:8bit;b:color", "out_mapping": "y:float;z:16bit"},
        )
        self.assertEqual(f.in_data_types, {"a": DataType.DT_8_BIT, "b": DataType.DT_COLOR})
        self.assertEqual(f.out_data_types, {"y": DataType.DT_DOUBLE, "z": DataType.DT_16_BIT})

    def test_malformed_entries_skipped_and_do_not_raise(self) -> None:
        """A corrupt show file must still load; bad entries are logged and dropped."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA,
            filter_id="lua",
            filter_configurations={
                # valid, no-separator, empty-name, unknown-dtype, duplicate-name
                "in_mapping": "good:8bit;badentry;:nokey;odd:unknown_dtype;good:16bit",
                "out_mapping": "other:color",
            },
        )
        # Only the first "good" entry survived; its data type is 8bit (duplicate ignored)
        self.assertEqual(f.in_data_types, {"good": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"other": DataType.DT_COLOR})

    def test_update_filter_configuration_rebuilds_terminals(self) -> None:
        """Writing a new mapping via update_filter_configuration re-runs the parse."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA, filter_id="lua"
        )
        self.assertEqual(f.out_data_types, {})
        f.update_filter_configuration("out_mapping", "p:float")
        self.assertEqual(f.out_data_types, {"p": DataType.DT_DOUBLE})

    def test_node_derives_lua_terminals_and_syncs_on_settings_change(self) -> None:
        """End-to-end: construct a Lua node, mutate config directly, call base rebuild+sync."""
        from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode

        scene = self._make_scene()
        # Pre-populate the scene filter path through node to simulate interactive creation.
        node = LuaFilterNode(model=scene, name="lua")
        self.assertEqual(set(node.inputs().keys()), set())
        self.assertEqual(set(node.outputs().keys()), set())
        # Simulate the FilterSettingsItem flow: dict mutation + update_node_after_settings_changed.
        node.filter.filter_configurations["in_mapping"] = "a:8bit"
        node.filter.filter_configurations["out_mapping"] = "y:color"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"a"})
        self.assertEqual(set(node.outputs().keys()), {"y"})
        # Removing a channel via a new mapping should remove the terminal from pyqtgraph.
        node.filter.filter_configurations["out_mapping"] = ""
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.outputs().keys()), set())

    def test_settings_change_preserves_unrelated_connections(self) -> None:
        """A terminal diff must only sever connections on removed terminals.

        Connections on terminals that survive the diff (same name, both before and after)
        must stay intact — both at the pyqtgraph level and at the model's channel_links
        level. This guards against a naive "clear all then re-add" implementation that
        would silently drop user-made wiring.
        """
        from unittest.mock import MagicMock

        from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode

        scene = self._make_scene()
        src = LuaFilterNode(model=scene, name="src")
        src.filter.filter_configurations["out_mapping"] = "a:8bit;b:8bit;c:8bit"
        src.update_node_after_settings_changed()

        dst = LuaFilterNode(model=scene, name="dst")
        dst.filter.filter_configurations["in_mapping"] = "xa:8bit;xb:8bit;xc:8bit"
        dst.update_node_after_settings_changed()

        # Install three connections without the pyqtgraph graphics stack. A mock stands in
        # for the ConnectionItem; Terminal.disconnectFrom only requires ``.close()`` on it,
        # and the terminals' ``connected()`` / ``disconnected()`` hooks drive the model-side
        # channel_links updates we care about.
        def connect(out_term, in_term) -> None:
            item = MagicMock()
            out_term._connections[in_term] = item
            in_term._connections[out_term] = item
            out_term.connected(in_term)
            in_term.connected(out_term)

        connect(src.outputs()["a"], dst.inputs()["xa"])
        connect(src.outputs()["b"], dst.inputs()["xb"])
        connect(src.outputs()["c"], dst.inputs()["xc"])
        self.assertEqual(
            dict(dst.filter.channel_links), {"xa": "src:a", "xb": "src:b", "xc": "src:c"}
        )

        a_term_before = src.outputs()["a"]
        c_term_before = src.outputs()["c"]

        # Remove only the middle output. 'a' and 'c' must survive without disturbance.
        src.filter.filter_configurations["out_mapping"] = "a:8bit;c:8bit"
        src.update_node_after_settings_changed()

        self.assertEqual(set(src.outputs().keys()), {"a", "c"})
        # Terminal objects for surviving ports are preserved — the diff did not re-create them.
        self.assertIs(src.outputs()["a"], a_term_before)
        self.assertIs(src.outputs()["c"], c_term_before)
        # Model-side channel_links reflect the severed connection on xb and keep the rest.
        self.assertEqual(dst.filter.channel_links["xa"], "src:a")
        self.assertEqual(dst.filter.channel_links["xc"], "src:c")
        self.assertEqual(dst.filter.channel_links["xb"], "")
        # pyqtgraph-side connections: xa and xc still linked, xb severed.
        self.assertEqual(len(dst.inputs()["xa"].connections()), 1)
        self.assertEqual(len(dst.inputs()["xc"].connections()), 1)
        self.assertEqual(len(dst.inputs()["xb"].connections()), 0)

    def test_settings_change_adds_new_terminal_without_touching_existing_connections(self) -> None:
        """Adding a brand-new terminal must leave previously-wired terminals alone."""
        from unittest.mock import MagicMock

        from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode

        scene = self._make_scene()
        src = LuaFilterNode(model=scene, name="src")
        src.filter.filter_configurations["out_mapping"] = "a:8bit"
        src.update_node_after_settings_changed()

        dst = LuaFilterNode(model=scene, name="dst")
        dst.filter.filter_configurations["in_mapping"] = "xa:8bit"
        dst.update_node_after_settings_changed()

        item = MagicMock()
        src.outputs()["a"]._connections[dst.inputs()["xa"]] = item
        dst.inputs()["xa"]._connections[src.outputs()["a"]] = item
        src.outputs()["a"].connected(dst.inputs()["xa"])
        dst.inputs()["xa"].connected(src.outputs()["a"])

        a_term_before = src.outputs()["a"]

        # Add a new output alongside the existing one.
        src.filter.filter_configurations["out_mapping"] = "a:8bit;new_output:color"
        src.update_node_after_settings_changed()

        self.assertEqual(set(src.outputs().keys()), {"a", "new_output"})
        self.assertIs(src.outputs()["a"], a_term_before)
        self.assertEqual(dst.filter.channel_links["xa"], "src:a")
        self.assertEqual(len(dst.inputs()["xa"].connections()), 1)


class AggregatingSubclassTests(unittest.TestCase):
    """Per-type assertions for the native aggregating subclasses migrated in PR 9.

    The virtual-filter ``VFILTER_COLOR_MIXER`` keeps its node-side aggregating behaviour
    until the v-filter pass and is not covered here.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_input_count_populates_two_inputs(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_SUM_8BIT, filter_id="s"
        )
        self.assertEqual(f.filter_configurations["input_count"], "2")
        self.assertEqual(f.in_data_types, {"0": DataType.DT_8_BIT, "1": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"value": DataType.DT_8_BIT})
        self.assertEqual(f.default_values, {"0": "0", "1": "0"})

    def test_data_type_per_subclass(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_SUM_8BIT, DataType.DT_8_BIT, "0"),
            (FilterTypeEnumeration.FILTER_SUM_16BIT, DataType.DT_16_BIT, "0"),
            (FilterTypeEnumeration.FILTER_SUM_FLOAT, DataType.DT_DOUBLE, "0.0"),
            (FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV, DataType.DT_COLOR, "0,0,0"),
            (FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB, DataType.DT_COLOR, "0,0,0"),
            (FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATIVE_RGB, DataType.DT_COLOR, "0,0,0"),
        ]
        for ft, expected_dt, expected_default in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"a_{ft.name}")
                self.assertEqual(f.in_data_types["0"], expected_dt)
                self.assertEqual(f.out_data_types["value"], expected_dt)
                self.assertEqual(f.default_values["0"], expected_default)

    def test_input_count_three_populates_three_inputs(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV,
            filter_id="m",
            filter_configurations={"input_count": "3"},
        )
        self.assertEqual(set(f.in_data_types.keys()), {"0", "1", "2"})
        for key in ("0", "1", "2"):
            self.assertEqual(f.in_data_types[key], DataType.DT_COLOR)
            self.assertEqual(f.default_values[key], "0,0,0")

    def test_invalid_input_count_falls_back_to_zero(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SUM_FLOAT,
            filter_id="s",
            filter_configurations={"input_count": "garbage"},
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.filter_configurations["input_count"], "0")

    def test_changing_input_count_syncs_pyqtgraph_terminals(self) -> None:
        """Dynamic rebuild: shrink from 3 inputs to 1 via update_node_after_settings_changed."""
        from view.show_mode.editor.nodes.impl.arithmetics import Sum8BitNode

        scene = self._make_scene()
        node = Sum8BitNode(model=scene, name="s")
        node.filter.filter_configurations["input_count"] = "3"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"0", "1", "2"})
        node.filter.filter_configurations["input_count"] = "1"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"0"})
        self.assertEqual(set(node.outputs().keys()), {"value"})


class EventSchedulerTests(unittest.TestCase):
    """Per-type assertions for the EventScheduler subclass migrated in PR 10."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_event_scheduler_defaults(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_EVENT_SCHEDULER, filter_id="e"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.filter_configurations["event_data"], "")
        self.assertEqual(f.initial_parameters["length"], "0")
        self.assertEqual(f.initial_parameters["update_triggers"], "")
        self.assertEqual(f.initial_parameters["step"], "0")
        self.assertEqual(f.initial_parameters["synchronization_target"], "0,0")


class UniverseOutputTests(unittest.TestCase):
    """Per-type assertions for the UniverseOutput subclass migrated in PR 10.

    The universe filter is dynamic: every non-``"universe"`` config key becomes an 8-bit
    input terminal. The node-side ``UniverseNode`` keeps interactive add/remove behaviour.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_empty_config_yields_no_inputs(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT, filter_id="u"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})

    def test_configs_populate_inputs_excluding_universe_key(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT,
            filter_id="u",
            filter_configurations={"universe": "3", "input_1": "0", "fixture_a": "17"},
        )
        self.assertEqual(f.filter_configurations["universe"], "3")
        self.assertEqual(set(f.in_data_types.keys()), {"input_1", "fixture_a"})
        for key in ("input_1", "fixture_a"):
            self.assertEqual(f.in_data_types[key], DataType.DT_8_BIT)
            self.assertEqual(f.default_values[key], "0")

    def test_fresh_universe_node_seeds_default_universe_id_and_input(self) -> None:
        from view.show_mode.editor.nodes.impl.universenode import UniverseNode

        scene = self._make_scene()
        node = UniverseNode(model=scene, name="Universe0")
        self.assertEqual(node.filter.filter_configurations["universe"], "1")
        self.assertEqual(node.filter.filter_configurations["input_1"], "0")
        self.assertEqual(set(node.inputs().keys()), {"input_1"})

    def test_universe_node_add_input_updates_model_and_terminals(self) -> None:
        from view.show_mode.editor.nodes.impl.universenode import UniverseNode

        scene = self._make_scene()
        node = UniverseNode(model=scene, name="Universe0")
        node.addInput()
        self.assertIn("input_2", node.inputs())
        self.assertEqual(node.filter.filter_configurations["input_2"], "1")
        self.assertEqual(node.filter.in_data_types["input_2"].value, 1)  # DT_8_BIT

    def test_universe_node_remove_terminal_clears_config_and_model(self) -> None:
        from view.show_mode.editor.nodes.impl.universenode import UniverseNode

        scene = self._make_scene()
        node = UniverseNode(model=scene, name="Universe0")
        node.addInput()  # adds input_2
        self.assertIn("input_2", node.filter.filter_configurations)
        node.removeTerminal(node.inputs()["input_2"])
        self.assertNotIn("input_2", node.filter.filter_configurations)
        self.assertNotIn("input_2", node.filter.in_data_types)


class FixtureToFilterRegressionTests(unittest.TestCase):
    """Guard against the "fixture-created filters have no ports" regression.

    ``place_fixture_filters_in_scene`` used to construct native filters via a direct
    ``Filter(...)`` call. After the subclass migrations the bare ``Filter`` has no
    ``_rebuild_io`` and lands with empty ``in_data_types`` / ``out_data_types``, which
    surfaces as port-less editor nodes. These tests pin the fix: every filter the fixture
    helper creates must come back with its I/O signature populated.
    """

    def _make_scene_and_page(self):
        from model import BoardConfiguration, Scene
        from model.scene import FilterPage

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        page = FilterPage(scene)
        scene._filter_pages.append(page)
        return scene, page

    @staticmethod
    def _make_drgbw_fixture_stub():
        """Minimal stub providing the attributes ``place_fixture_filters_in_scene`` reads.

        Mirrors a 5-channel Dimmer / Red / Green / Blue / White fixture.
        """

        class _ChannelStub:
            def __init__(self, name: str) -> None:
                self.name = name

        class _FixtureStub:
            def __init__(self) -> None:
                self.parent_universe = 1
                self.start_index = 0
                self.name = "GenericDRGBW"
                self._channels = tuple(_ChannelStub(n) for n in ("Dimmer", "Red", "Green", "Blue", "White"))

            @property
            def channel_length(self) -> int:
                return len(self._channels)

            @property
            def fixture_channels(self):  # noqa: ANN202
                return self._channels

            def get_fixture_channel(self, index: int):  # noqa: ANN202
                return self._channels[index]

        return _FixtureStub()

    def test_drgbw_fixture_produces_filters_with_populated_io(self) -> None:
        """Regression: every placed filter must have a non-empty I/O signature."""
        from model.filter import DataType, FilterTypeEnumeration
        from view.show_mode.editor.show_browser.fixture_to_filter import place_fixture_filters_in_scene

        scene, page = self._make_scene_and_page()
        fixture = self._make_drgbw_fixture_stub()

        self.assertTrue(place_fixture_filters_in_scene(fixture, page))

        # Group filters by type for focused assertions.
        by_type: dict[int, list] = {}
        for f in scene.filters:
            by_type.setdefault(int(f.filter_type), []).append(f)

        # Universe output: five inputs, one per channel, each DT_8_BIT; no outputs.
        universe_filters = by_type.get(int(FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT), [])
        self.assertEqual(len(universe_filters), 1)
        uf = universe_filters[0]
        self.assertEqual(set(uf.in_data_types.keys()), {"Dimmer", "Red", "Green", "Blue", "White"})
        for dt in uf.in_data_types.values():
            self.assertEqual(dt, DataType.DT_8_BIT)
        self.assertEqual(uf.filter_configurations["universe"], "1")

        # Colour-to-RGBW adapter: one input ``value`` DT_COLOR, four 8-bit outputs r/g/b/w.
        rgbw_filters = by_type.get(int(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW), [])
        self.assertEqual(len(rgbw_filters), 1)
        rgbw = rgbw_filters[0]
        self.assertEqual(rgbw.in_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(set(rgbw.out_data_types.keys()), {"r", "g", "b", "w"})

        # Dimmer brightness mixin v-filter (unchanged path through its own ctor).
        dimmer_vfilters = by_type.get(int(FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN), [])
        self.assertEqual(len(dimmer_vfilters), 1)
        self.assertTrue(len(dimmer_vfilters[0].out_data_types) > 0)


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


class FaderSubclassTests(unittest.TestCase):
    """Per-type assertions for the native fader subclasses migrated in PR 12."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_fader_raw_signature_and_defaults(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_FADER_RAW, filter_id="r"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(
            f.out_data_types,
            {"primary": DataType.DT_16_BIT, "secondary": DataType.DT_16_BIT},
        )
        self.assertEqual(f.filter_configurations["set_id"], "")
        self.assertEqual(f.filter_configurations["column_id"], "")

    def test_hsi_faders_signatures_and_default_ignore_main_brightness(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            (FilterTypeEnumeration.FILTER_FADER_HSI, {"color"}),
            (FilterTypeEnumeration.FILTER_FADER_HSIA, {"color", "amber"}),
            (FilterTypeEnumeration.FILTER_FADER_HSIU, {"color", "uv"}),
            (FilterTypeEnumeration.FILTER_FADER_HSIAU, {"color", "amber", "uv"}),
        ]
        for ft, expected_out in cases:
            with self.subTest(filter_type=ft.name):
                f = construct_filter_instance(scene=scene, filter_type=ft, filter_id=f"f_{ft.name}")
                self.assertEqual(set(f.out_data_types.keys()), expected_out)
                self.assertEqual(f.out_data_types["color"], DataType.DT_COLOR)
                self.assertEqual(f.filter_configurations["ignore_main_brightness_control"], "false")
                self.assertEqual(f.filter_configurations["set_id"], "")
                self.assertEqual(f.filter_configurations["column_id"], "")

    def test_main_brightness_signature(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS, filter_id="mb"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {"brightness": DataType.DT_16_BIT})
        self.assertFalse(f.configuration_supported)

    def test_loaded_configs_override_defaults(self) -> None:
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_FADER_HSIA,
            filter_id="f",
            filter_configurations={
                "set_id": "main",
                "column_id": "fader_7",
                "ignore_main_brightness_control": "true",
            },
        )
        self.assertEqual(f.filter_configurations["set_id"], "main")
        self.assertEqual(f.filter_configurations["column_id"], "fader_7")
        self.assertEqual(f.filter_configurations["ignore_main_brightness_control"], "true")


class CueFilterTests(unittest.TestCase):
    """Per-type assertions for the CueFilter v-filter migrated in PR 13.

    The cue v-filter now derives its ``out_data_types`` from ``filter_configurations["mapping"]``
    at construction time, so loaded shows have fully-populated terminals before the editor view
    opens.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_without_mapping(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.VFILTER_CUES, filter_id="c")
        self.assertEqual(
            f.in_data_types,
            {"time": DataType.DT_DOUBLE, "time_scale": DataType.DT_DOUBLE},
        )
        self.assertEqual(f.out_data_types, {})
        self.assertEqual(f.default_values["time_scale"], "1.0")
        self.assertEqual(f.filter_configurations["mapping"], "")
        self.assertEqual(f.filter_configurations["end_handling"], "")
        self.assertEqual(f.filter_configurations["cuelist"], "")
        self.assertEqual(f.gui_update_keys["run_mode"], ["play", "pause", "to_next_cue", "stop"])
        self.assertEqual(f.gui_update_keys["run_cue"], DataType.DT_16_BIT)

    def test_mapping_populates_typed_outputs(self) -> None:
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="c",
            filter_configurations={"mapping": "a:8bit;b:color;c:float;d:16bit"},
        )
        self.assertEqual(
            f.out_data_types,
            {
                "a": DataType.DT_8_BIT,
                "b": DataType.DT_COLOR,
                "c": DataType.DT_DOUBLE,
                "d": DataType.DT_16_BIT,
            },
        )

    def test_malformed_entries_skipped_and_valid_ones_kept(self) -> None:
        """Loader-time robustness: bad mapping entries must be dropped, not raise."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="c",
            filter_configurations={"mapping": "good:8bit;nocolonentry;bad:unknown_type;ok:color"},
        )
        self.assertEqual(
            f.out_data_types, {"good": DataType.DT_8_BIT, "ok": DataType.DT_COLOR}
        )

    def test_mapping_change_shrinks_outputs_on_rebuild(self) -> None:
        """Removing entries from ``mapping`` must drop the corresponding outputs after rebuild."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_CUES,
            filter_id="c",
            filter_configurations={"mapping": "a:8bit;b:color"},
        )
        self.assertEqual(set(f.out_data_types.keys()), {"a", "b"})
        f.update_filter_configuration("mapping", "a:8bit")
        self.assertEqual(f.out_data_types, {"a": DataType.DT_8_BIT})


class NodeTerminalsFromFilterTests(unittest.TestCase):
    """When a node passes ``terminals=None``, the base derives terminals from the filter.

    PR 1 removes the explicit ``terminals=`` arg from the migrated adapter nodes, so this
    test guards that the pyqtgraph Node ends up with the exact terminal set that the
    filter's subclass declared.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_adapter_node_derives_terminals_from_filter(self) -> None:
        from view.show_mode.editor.nodes.impl.adapters import AdapterColorToRGBWANode

        scene = self._make_scene()
        node = AdapterColorToRGBWANode(model=scene, name="rgbwa")
        # pyqtgraph exposes inputs/outputs dicts
        self.assertEqual(set(node.inputs().keys()), {"value"})
        self.assertEqual(set(node.outputs().keys()), {"r", "g", "b", "w", "a"})
        self.assertFalse(node.filter.configuration_supported)


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
