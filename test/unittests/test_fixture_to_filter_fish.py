"""Fish-side execution test for a hand-built DRGBW universe-output filter.

Builds the universe-output configuration that
:func:`view.show_mode.editor.show_browser.fixture_to_filter.place_fixture_filters_in_scene`
would produce for a 5-channel DRGBW fixture (Dimmer + Red + Green + Blue + White) and
submits the resulting scene to a live fish instance via
:func:`test.unittests.utilities.execute_board_configuration`. The 8-bit dimmer input and
colour-to-RGBW chain are wired directly to constants — no
:class:`DimmerGlobalBrightnessMixinVFilter` is required for this layout.

Guards against regressions where the universe-output filter configuration fails fish's
show-file parsing (most recently when the fixture helper constructed native filters with a
bare ``Filter(...)`` and the resulting instances landed without their I/O signature).

Requires a local ``test/unittests/config.py`` with ``FISH_EXEC_PATH`` pointing to a fish
binary; the module is unimportable without it, matching the pattern used by
``test_dimmer_brightness_mixin_vfilter``.
"""

import logging
import unittest
from logging import basicConfig, getLogger

import proto.UniverseControl_pb2
from model import BoardConfiguration, Scene
from model.filter import FilterTypeEnumeration
from model.filters.factory import construct_filter_instance
from model.universe import Universe
from test.unittests.utilities import execute_board_configuration

logger = getLogger(__name__)


class FixtureToFilterFishExecutionTest(unittest.TestCase):
    """Apply a DRGBW universe-output configuration to fish and assert it is accepted."""

    # TODO once the DimmerGlobalBrightnessMixinVFilter resolve-disabled-port bug is merged
    #   from its separate branch, extend this test to cover a 16-bit dimmer fixture driven
    #   through the full place_fixture_filters_in_scene path (double-channel dimmer + mixin
    #   + 16-bit constant on the mixin's input).
    def test_drgbw_8bit_universe_filter_applies_to_fish(self) -> None:
        """Hand-wire a DRGBW universe filter with constant-driven inputs and submit to fish."""
        basicConfig(level=logging.DEBUG)

        show = BoardConfiguration()

        # Fish rejects filters whose "universe" configuration does not match a known universe,
        # so declare a dummy ArtNet universe pointing at localhost before any filter touches it.
        # Universe id 1 matches the universe filter below.
        Universe(
            proto.UniverseControl_pb2.Universe(
                id=1,
                remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                    ip_address="127.0.0.1", port=6454, universe_on_device=0
                ),
            )
        )

        scene = Scene(0, "DRGBW 8-bit universe filter test", show)
        show._add_scene(scene)
        # Accessing pages lazily materialises the default FilterPage attached to the scene.
        _ = scene.pages[0]

        # Universe filter for a DRGBW fixture patched at universe 1, start address 1.
        universe = construct_filter_instance(
            scene=scene,
            filter_id="universe-output_drgbw",
            filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT,
            pos=(0, 0),
            filter_configurations={
                "universe": "1",
                "Dimmer": "1",
                "Red": "2",
                "Green": "3",
                "Blue": "4",
                "White": "5",
            },
        )
        scene.append_filter(universe)

        # 8-bit constant drives the Dimmer channel directly.
        const_dimmer = construct_filter_instance(
            scene=scene,
            filter_id="dimmer_input_8bit",
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
            pos=(-100, 0),
            initial_parameters={"value": "127"},
        )
        scene.append_filter(const_dimmer)
        universe.channel_links["Dimmer"] = f"{const_dimmer.filter_id}:value"

        # Colour constant feeds a Colour-to-RGBW adapter whose outputs drive the colour
        # channels on the universe filter.
        const_color = construct_filter_instance(
            scene=scene,
            filter_id="color_input",
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
            pos=(-150, 100),
            initial_parameters={"value": "180,1.0,1.0"},
        )
        scene.append_filter(const_color)

        color_to_rgbw = construct_filter_instance(
            scene=scene,
            filter_id="color_to_rgbw",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW,
            pos=(-50, 100),
        )
        scene.append_filter(color_to_rgbw)
        color_to_rgbw.channel_links["value"] = f"{const_color.filter_id}:value"

        for channel, port in (("Red", "r"), ("Green", "g"), ("Blue", "b"), ("White", "w")):
            universe.channel_links[channel] = f"{color_to_rgbw.filter_id}:{port}"

        self.assertTrue(execute_board_configuration(show))


if __name__ == "__main__":
    unittest.main()
