"""Per-type assertions for time-related filter subclasses."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class TimeSubclassTests(unittest.TestCase):
    """Per-type assertions for the native time-filter subclasses migrated in PR 7."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_time_input_signature(self) -> None:
        """TimeInput exposes no inputs and one DT_DOUBLE ``value`` output."""
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
        """EventCounter exposes a time input, two 16-bit outputs, and a default event config."""
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
        """Each delay subclass maps the ``value_in`` input and ``value`` output to its data type."""
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
        """On-delay and off-delay 8bit filters resolve to the same ``TimeDelay8Bit`` subclass."""
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
        """Loaded ``delay`` and unknown-future configs are preserved on the delay filter."""
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
