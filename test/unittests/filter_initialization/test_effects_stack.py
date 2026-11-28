"""Tests for the effects stack filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class EffectsStackTests(unittest.TestCase):
    """Smoke test for EffectsStack: no I/O to derive, just verify factory + node work."""

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_effects_stack_constructs_with_empty_io(self) -> None:
        """EffectsStack v-filter constructs via the factory with empty I/O dicts."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance
        from model.virtual_filters.effects_stacks.vfilter import EffectsStack

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.VFILTER_EFFECTSSTACK, filter_id="es"
        )
        self.assertIsInstance(f, EffectsStack)
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})
