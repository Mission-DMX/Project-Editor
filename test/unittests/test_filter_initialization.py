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
