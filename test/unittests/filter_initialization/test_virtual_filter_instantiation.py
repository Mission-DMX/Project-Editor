"""Tests for the virtual filter instantiation entry points."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


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
        """The dimmer brightness mixin v-filter must still produce at least one native filter."""
        from model.virtual_filters.range_adapters import DimmerGlobalBrightnessMixinVFilter

        scene = self._make_scene()
        mixin = DimmerGlobalBrightnessMixinVFilter(scene, "mixin", (0, 0))
        scene.append_filter(mixin)

        produced: list = []
        mixin.instantiate_filters(produced)
        self.assertGreater(len(produced), 0, "V-filter must produce at least one native filter")

    def test_sixteen_bit_to_float_range_still_instantiates(self) -> None:
        """The 16bit-to-float range v-filter must still produce two native filters when instantiated."""
        from model.virtual_filters.range_adapters import SixteenBitToFloatRange

        scene = self._make_scene()
        v = SixteenBitToFloatRange(scene, "r16", (0, 0))
        v.channel_links["value_in"] = "src:value"
        scene.append_filter(v)

        produced: list = []
        v.instantiate_filters(produced)
        self.assertEqual(len(produced), 2)
