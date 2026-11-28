"""Tests for the color mixer virtual filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class ColorMixerVFilterTests(unittest.TestCase):
    """Per-type assertions for ColorMixerVFilter migrated in PR 18."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_signature_and_method_hsv(self) -> None:
        """Default ColorMixerVFilter uses HSV with two color inputs and a color output."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER, filter_id="cm"
        )
        self.assertEqual(f.filter_configurations["method"], "hsv")
        self.assertEqual(f.filter_configurations["input_count"], "2")
        self.assertEqual(f.out_data_types, {"value": DataType.DT_COLOR})
        self.assertEqual(set(f.in_data_types.keys()), {"0", "1"})
        for key in ("0", "1"):
            self.assertEqual(f.in_data_types[key], DataType.DT_COLOR)
            self.assertEqual(f.default_values[key], "0,0,0")

    def test_input_count_three(self) -> None:
        """Setting ``input_count=3`` on the color mixer exposes three color inputs."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER,
            filter_id="cm",
            filter_configurations={"input_count": "3"},
        )
        self.assertEqual(set(f.in_data_types.keys()), {"0", "1", "2"})

    def test_instantiate_dispatches_to_native_mixer(self) -> None:
        """Methods map to the correct FILTER_COLOR_MIXER_* native type."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        cases = [
            ("hsv", FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV),
            ("hsv_red_sat", FilterTypeEnumeration.FILTER_COLOR_MIXER_HSV),
            ("additive_rgb", FilterTypeEnumeration.FILTER_COLOR_MIXER_ADDITIVE_RGB),
            ("normative_rgb", FilterTypeEnumeration.FILTER_COLOR_MIXER_NORMATIVE_RGB),
        ]
        for method, expected_type in cases:
            with self.subTest(method=method):
                f = construct_filter_instance(
                    scene=scene,
                    filter_type=FilterTypeEnumeration.VFILTER_COLOR_MIXER,
                    filter_id=f"cm_{method}",
                    filter_configurations={"method": method},
                )
                produced: list = []
                f.instantiate_filters(produced)
                self.assertEqual(len(produced), 1)
                self.assertEqual(int(produced[0].filter_type), int(expected_type))
                # Produced native has full I/O (headless invariant).
                self.assertEqual(set(produced[0].in_data_types.keys()), {"0", "1"})
