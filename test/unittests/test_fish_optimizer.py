"""Unit tests for :mod:`controller.file.serializing.fish_optimizer`.

The regression these pin down showed up when a hand-authored universe-output
filter declared a ``filterConfiguration`` for a DMX channel but no matching
``channellink``. The aggregator then stored the source as ``"None"`` and
emitted ``<channellink output_channel_id="None"/>``, which fish rejected as
an unresolved dependency and refused to schedule the whole scene.

The fix wires every unlinked slot to a shared ``const8bitval0`` filter and
coordinates with ``filter_serialization``'s defaults pass so that constant
is materialised exactly once.
"""

from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

from controller.file.serializing.fish_optimizer import SceneOptimizerModule
from model.filter import DataType, FilterTypeEnumeration


def _make_universe_filter(
    filter_id: str,
    universe: str,
    channel_links: dict[str, str | None],
    filter_configurations: dict[str, str],
) -> MagicMock:
    """Build a Filter-like mock accepted by :meth:`_substitute_universe_filter`."""
    f = MagicMock()
    f.filter_id = filter_id
    f.filter_type = FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT
    f.filter_configurations = {"universe": universe, **filter_configurations}
    # Real ``channel_links`` is a dict; ``.get()`` must return None for keys
    # the user left unwired so the aggregator sees the same shape it would in
    # a serialized show file.
    f.channel_links = dict(channel_links)
    return f


class UniverseOutputUnwiredFallbackTest(unittest.TestCase):
    """Verify universe-output fallback wiring for unwired configuration channels."""

    def test_unwired_channel_defaults_to_zero_constant(self) -> None:
        """An unwired config entry must land on ``const8bitval0:value``."""
        om = SceneOptimizerModule(replacing_enabled=True)
        universe_filter = _make_universe_filter(
            filter_id="universe-output_0-1_Stub",
            universe="0",
            channel_links={"Dimmer": "some_source:value"},
            filter_configurations={"Dimmer": "1", "Focus": "12"},  # Focus has no link
        )
        om._substitute_universe_filter(universe_filter)

        scene = ET.Element("scene")
        om.wrap_up(scene)

        emitted = {
            el.get("input_channel_id"): el.get("output_channel_id")
            for el in scene.iter("channellink")
        }
        # ``_substitute_universe_filter`` prefixes the input channel name with
        # the originating filter's id so distinct universe outputs don't collide
        # in the aggregated filter.
        self.assertEqual("some_source:value", emitted["universe-output_0-1_Stub__Dimmer"])
        self.assertEqual("const8bitval0:value", emitted["universe-output_0-1_Stub__Focus"])
        # The optimizer must have asked filter_serialization to materialise the
        # constant via the shared ``extra_default_values`` hand-off.
        self.assertEqual({"0"}, set(om.extra_default_values[DataType.DT_8_BIT]))

    def test_no_default_tracked_when_all_channels_wired(self) -> None:
        """When every config entry has a link, the fallback must stay silent."""
        om = SceneOptimizerModule(replacing_enabled=True)
        universe_filter = _make_universe_filter(
            filter_id="universe-output_wired",
            universe="0",
            channel_links={"Dimmer": "src:value", "Focus": "src:other"},
            filter_configurations={"Dimmer": "1", "Focus": "2"},
        )
        om._substitute_universe_filter(universe_filter)

        scene = ET.Element("scene")
        om.wrap_up(scene)

        self.assertEqual({}, om.extra_default_values)
        emitted = {
            el.get("input_channel_id"): el.get("output_channel_id")
            for el in scene.iter("channellink")
        }
        self.assertEqual(
            {"universe-output_wired__Dimmer": "src:value",
             "universe-output_wired__Focus": "src:other"},
            emitted,
        )

    def test_fallback_survives_aggregation_of_multiple_universe_filters(self) -> None:
        """Both filters' unlinked channels must land on the same constant."""
        om = SceneOptimizerModule(replacing_enabled=True)
        om._substitute_universe_filter(_make_universe_filter(
            filter_id="universe-output_a",
            universe="0",
            channel_links={},
            filter_configurations={"A": "1", "B": "2"},
        ))
        om._substitute_universe_filter(_make_universe_filter(
            filter_id="universe-output_b",
            universe="0",
            channel_links={"C": "live:value"},
            filter_configurations={"C": "3", "D": "4"},
        ))

        scene = ET.Element("scene")
        om.wrap_up(scene)

        emitted = {
            el.get("input_channel_id"): el.get("output_channel_id")
            for el in scene.iter("channellink")
        }
        # A, B and D are unlinked; C is live.
        for k in ("universe-output_a__A", "universe-output_a__B", "universe-output_b__D"):
            self.assertEqual("const8bitval0:value", emitted[k])
        self.assertEqual("live:value", emitted["universe-output_b__C"])
        self.assertEqual({"0"}, set(om.extra_default_values[DataType.DT_8_BIT]))


class FilterSerializationIntegrationTest(unittest.TestCase):
    """End-to-end check that the extra_default_values hand-off emits the const once."""

    def test_const8bitval0_filter_emitted_exactly_once(self) -> None:
        """The defaults pass must materialise the constant filter and not duplicate it."""
        from controller.file.serializing.filter_serialization import (
            create_channel_mappings_for_filter_set_for_fish,
        )

        om = SceneOptimizerModule(replacing_enabled=True)
        om._substitute_universe_filter(_make_universe_filter(
            filter_id="universe-output_unwired",
            universe="0",
            channel_links={},
            filter_configurations={"Focus": "1"},
        ))

        scene = ET.Element("scene")
        create_channel_mappings_for_filter_set_for_fish(True, om, scene)

        const_filters = [
            el for el in scene.iter("filter")
            if el.get("id") == "const8bitval0"
        ]
        self.assertEqual(1, len(const_filters), "const8bitval0 must appear once")
        self.assertEqual(
            str(FilterTypeEnumeration.FILTER_CONSTANT_8BIT),
            const_filters[0].get("type"),
        )
        initial = const_filters[0].find("initialParameters")
        self.assertIsNotNone(initial)
        self.assertEqual("value", initial.get("name"))
        self.assertEqual("0", initial.get("value"))


if __name__ == "__main__":
    unittest.main()
