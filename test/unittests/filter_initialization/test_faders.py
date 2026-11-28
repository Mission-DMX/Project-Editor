"""Per-type assertions for fader filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class FaderSubclassTests(unittest.TestCase):
    """Per-type assertions for the native fader subclasses migrated in PR 12."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_fader_raw_signature_and_defaults(self) -> None:
        """FaderRaw exposes primary/secondary 16-bit outputs and empty set/column configs."""
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
        """HSI fader subclasses expose the ``color`` output plus optional amber/uv ports."""
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
        """MainBrightness exposes a single 16-bit ``brightness`` output and no inputs."""
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
        """Loaded fader configs (set_id, column_id, ignore_main_brightness) must override defaults."""
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
