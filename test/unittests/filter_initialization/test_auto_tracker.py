"""Tests for the auto-tracker filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class AutoTrackerFilterTests(unittest.TestCase):
    """Per-type assertions for AutoTrackerFilter migrated in PR 14."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_zero_trackers_still_exposes_one_pan_tilt_pair(self) -> None:
        """Preserves the pre-migration ``trackers + 1`` loop semantics."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_AUTOTRACKER, filter_id="at"
        )
        min_id = f.get_min_brightness_filter_id()
        self.assertIn(min_id, f.out_data_types)
        self.assertEqual(f.out_data_types[min_id], DataType.DT_DOUBLE)
        self.assertIn("Tracker0_Pan", f.out_data_types)
        self.assertIn("Tracker0_Tilt", f.out_data_types)

    def test_tracker_count_two_adds_more_outputs(self) -> None:
        """``trackercount=2`` yields pan/tilt outputs for three trackers (preserving the +1 loop)."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.VFILTER_AUTOTRACKER,
            filter_id="at",
            filter_configurations={"trackercount": "2"},
        )
        for i in range(3):  # 2 + 1 per the preserved loop semantics
            self.assertIn(f"Tracker{i}_Pan", f.out_data_types)
            self.assertIn(f"Tracker{i}_Tilt", f.out_data_types)
