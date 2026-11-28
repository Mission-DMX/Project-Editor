"""Tests for the event scheduler filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class EventSchedulerTests(unittest.TestCase):
    """Per-type assertions for the EventScheduler subclass migrated in PR 10."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_event_scheduler_defaults(self) -> None:
        """EventScheduler has empty I/O, blank event_data config, and seeded initial parameters."""
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
