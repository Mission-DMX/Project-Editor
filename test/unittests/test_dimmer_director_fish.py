"""Fish-instantiation test for the Dimmer Director filter (type 84).

Builds a minimal show with one dimmer director plus the inputs its channel-link resolver
needs, then runs the shared ``execute_board_configuration`` harness. The harness starts a
fish binary, uploads the serialized show file and reports the final status fish produced;
the test passes iff fish accepts the configuration without an error.

This test lives in its own module because ``execute_board_configuration`` constructs its
own ``QApplication``; the roundtrip test in ``test_dimmer_director_filter.py`` needs one
at import time, and keeping the two tests in a shared module causes a shiboken-level
collision at ``QApplication([])`` time.
"""
from __future__ import annotations

import logging
import unittest
from logging import basicConfig, getLogger

from model import BoardConfiguration, Filter, Scene
from model.filter import FilterTypeEnumeration
from model.filters.dimmer_director import DimmerDirectorFilter, EffectCurveMode
from test.unittests.utilities import execute_board_configuration

logger = getLogger(__name__)


class DimmerDirectorFishInstantiationTest(unittest.TestCase):
    """Verify fish accepts a dimmer director's serialized configuration."""

    def test_fish_accepts_serialized_filter(self) -> None:
        """Build a small dimmer director with constant inputs and run it through fish."""
        basicConfig(level=logging.DEBUG)
        show = self._prepare_show_config()
        self.assertTrue(
            execute_board_configuration(show),
            "fish rejected the dimmer director configuration",
        )

    @staticmethod
    def _prepare_show_config() -> BoardConfiguration:
        show = BoardConfiguration(show_name="dimmer director fish test")
        scene = Scene(0, "Dimmer Director Fish Scene", show)
        show._add_scene(scene)

        dd = DimmerDirectorFilter(
            scene=scene,
            filter_id="dd_fish_test",
            filter_type=FilterTypeEnumeration.FILTER_DIMMER_DIRECTOR,
            pos=(0.0, 0.0),
        )

        # Two groups with small X*Y*Z footprints keep the fish-side cell matrix tiny.
        g1 = dd.add_group("wash")
        g1.x, g1.y, g1.z = 2, 1, 1
        dd.update_group(0, g1)
        g2 = dd.add_group("floor")
        g2.x, g2.y, g2.z = 1, 1, 1
        dd.update_group(1, g2)

        # One REPEAT effect curve (eight-sample sawtooth) and one LIN dimmer curve.
        eff = dd.add_effect_curve("sweep")
        eff.mode = EffectCurveMode.REPEAT
        eff.samples = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75]
        dd.add_dimmer_curve("lin")

        # Initial-parameter driven curve activation on scene enter.
        dd.initial_parameters["active_effect"] = "wash:0"
        dd.initial_parameters["active_dimmer"] = "wash:0"

        scene.append_filter(dd)

        # Each group's main dimmer input needs a 16bit source so fish's channel-link
        # resolver can wire it up. We feed every group from a constant filter.
        for i, group_name in enumerate(("wash", "floor")):
            const = Filter(
                scene,
                f"input_{group_name}",
                FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
                pos=(-50.0, i * 10.0),
            )
            const.initial_parameters["value"] = str(32000)
            scene.append_filter(const)
            dd.channel_links[group_name] = f"{const.filter_id}:value"
        return show


if __name__ == "__main__":
    unittest.main()
