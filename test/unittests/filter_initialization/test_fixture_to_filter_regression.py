"""Regression tests covering fixture-to-filter wiring."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


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
        from model.patching.fixture_channel import FixtureChannelType

        class _ChannelStub:
            def __init__(self, name: str, ch_type: FixtureChannelType) -> None:
                self.name = name
                self.type = ch_type
                self.channel_template = None
                self.is_fine = False

        class _FixtureStub:
            def __init__(self) -> None:
                self.parent_universe = 1
                self.start_index = 0
                self.name = "GenericDRGBW"
                self._channels = (
                    _ChannelStub("Dimmer", FixtureChannelType.INTENSITY),
                    _ChannelStub("Red", FixtureChannelType.RED),
                    _ChannelStub("Green", FixtureChannelType.GREEN),
                    _ChannelStub("Blue", FixtureChannelType.BLUE),
                    _ChannelStub("White", FixtureChannelType.WHITE),
                )

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
        from controller.show_manipulation.fixture_to_filter import place_fixture_filters_in_scene

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
