"""Integration test for the channel_scope request/reply signal chain."""

from __future__ import annotations

import logging
import math
import unittest
from logging import basicConfig, getLogger
from time import sleep

from model import BoardConfiguration, Broadcaster, Filter, Scene
from model.color_hsi import ColorHSI
from model.filter import FilterTypeEnumeration
from test.unittests.utilities import execute_board_configuration

logger = getLogger(__name__)


class ScopeSignalChainTest(unittest.TestCase):
    """Verify request_channel_scope reaches fish and the reply parses for every data type."""

    def test_scope_signal_chain(self) -> None:
        basicConfig(level=logging.DEBUG)

        show = BoardConfiguration()
        scene = Scene(0, "Test Scene for scope signal chain", show)
        show._add_scene(scene)

        probes: list[tuple[str, str, str]] = [
            ("const_8bit", str(FilterTypeEnumeration.FILTER_CONSTANT_8BIT.value), "42"),
            ("const_16bit", str(FilterTypeEnumeration.FILTER_CONSTANT_16_BIT.value), "4242"),
            ("const_float", str(FilterTypeEnumeration.FILTER_CONSTANT_FLOAT.value), "0.5"),
            ("const_color", str(FilterTypeEnumeration.FILTER_CONSTANT_COLOR.value), "120.0,0.75,1.0"),
        ]

        filter_ids: list[str] = []
        for row, (filter_id, type_value, initial_value) in enumerate(probes):
            f = Filter(scene, filter_id, int(type_value), pos=(0, row * 10))
            f.initial_parameters["value"] = initial_value
            scene.append_filter(f)
            filter_ids.append(filter_id)

        received: list[tuple[str, str]] = []
        Broadcaster().channel_scope_value_received.connect(
            lambda channel_id, current_value: received.append((channel_id, current_value))
        )

        def after_apply(nm, app) -> None:  # type: ignore[no-untyped-def]
            for filter_id in filter_ids:
                nm.request_channel_scope(f"{filter_id}:value")
            # Let fish reply before the evaluation phase runs.
            for _ in range(50):
                app.processEvents()
                sleep(0.01)

        ok = execute_board_configuration(show, after_apply=after_apply)
        self.assertTrue(ok, "fish execution reported an error")

        values_by_id: dict[str, str] = {}
        for channel_id, current_value in received:
            values_by_id[channel_id] = current_value

        for filter_id in filter_ids:
            self.assertIn(f"{filter_id}:value", values_by_id,
                          f"no channel_scope reply received for {filter_id}")

        self.assertEqual(int(values_by_id["const_8bit:value"]), 42)
        self.assertEqual(int(values_by_id["const_16bit:value"]), 4242)
        self.assertTrue(math.isclose(float(values_by_id["const_float:value"]), 0.5, abs_tol=0.01),
                        f"float value out of tolerance: {values_by_id['const_float:value']}")
        color = ColorHSI.from_filter_str(values_by_id["const_color:value"], strict=True)
        self.assertTrue(math.isclose(color.hue, 120.0, abs_tol=0.5))
        self.assertTrue(math.isclose(color.saturation, 0.75, abs_tol=0.01))
        self.assertTrue(math.isclose(color.intensity, 1.0, abs_tol=0.01))


if __name__ == "__main__":
    unittest.main()
