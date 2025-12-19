"""Unit test for dimmer brightness mixin."""
import logging
import unittest
from logging import getLogger, basicConfig

from model import BoardConfiguration, Scene, Filter
from model.filter import FilterTypeEnumeration
from model.virtual_filters.range_adapters import DimmerGlobalBrightnessMixinVFilter
from test.unittests.utilities import execute_board_configuration


logger = getLogger(__name__)


class DimmerBrightnessMixinTest(unittest.TestCase):
    """Unit test for dimmer brightness mixin."""

    def _prepare_show_config(self) -> tuple[BoardConfiguration, list[tuple[str, float]]]:
        show = BoardConfiguration()
        scene = Scene(0, "Test Scene for dimmer brightness mixin", show)
        show._add_scene(scene)
        output_list = []
        row: int = 0

        def create_input(method: str, mf: DimmerGlobalBrightnessMixinVFilter, is_mixin: bool) -> str:
            mf.filter_configurations["input_method_mixin" if is_mixin else "input_method"] = method.replace("-", "")
            if "-" not in method:
                input_filter = Filter(
                    scene,
                    f"input_filter_{row}_{method}_{"mixin" if is_mixin else "input"}",
                    FilterTypeEnumeration.FILTER_CONSTANT_8BIT if method == "8bit" else FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
                    pos=(-10, row * 15 + (5 if is_mixin else -5))
                )
                input_filter.initial_parameters["value"] = str(255 / 2) if method == "8bit" else str(65565 / 2)
                scene.append_filter(input_filter)
                mf.channel_links["mixin" if is_mixin else "input"] = f"{input_filter.filter_id}:value"

        def create_output(is_8b: bool):
            output_filter = Filter(
                scene, f"output_{"8b" if is_8b else "16b"}_{row}", FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT if is_8b else FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT,
                pos=(5, row * 15 + (-5 if is_8b else 5))
            )
            scene.append_filter(output_filter)
            output_filter.channel_links["value"] = mixin_filter.filter_id + (":dimmer_out8b" if is_8b else ":dimmer_out16b")
            expected_output = (255 if is_8b else 65565) * calculate_dimmer_val(input_method, mixin_method, has_offset)
            logger.info("Registering output %s => %s.", output_filter.filter_id, expected_output)
            output_list.append(
                (output_filter.filter_id, expected_output))

        def calculate_dimmer_val(in_m: str, mixin_m: str, has_offset: bool) -> float:
            in_stream = 1.0 if "-" in in_m else 0.5
            mixin_stream = 1.0
            offset_stream = 0.25 if has_offset else 0.0
            return max(0.0, min(1.0, in_stream * mixin_stream + offset_stream))

        for input_method in ["-8bit", "-16bit", "8bit", "16bit"]:
            for mixin_method in ["-8bit", "-16bit", "8bit", "16bit"]:
                for output_8b_enabled in [True, False]:
                    for output_16b_enabled in [True, False]:
                        for has_offset in [True, False]:
                            logger.info("Creating Config Row: %s, Input: %s, Mixin: %s, Out bit: %s, Out 16bit: %s, has Offset: %s", row, input_method, mixin_method, output_8b_enabled, output_16b_enabled, has_offset)
                            mixin_filter = DimmerGlobalBrightnessMixinVFilter(scene, f"mixin_filter_r{row}", (0, row * 15))
                            create_input(input_method, mixin_filter, False)
                            create_input(mixin_method, mixin_filter, True)

                            if has_offset:
                                offset_filter = Filter(
                                    scene, f"offset_filter_{row}", FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                                    pos=(-5, row * 15)
                                )
                                offset_filter.initial_parameters["value"] = "0.25"
                                scene.append_filter(offset_filter)
                                mixin_filter.channel_links["offset"] = offset_filter.filter_id + ":value"

                            if output_8b_enabled:
                                create_output(True)
                            if output_16b_enabled:
                                create_output(False)
                            row += 1
        return show, output_list

    def test_inst(self):
        """Test instanciation and results of v filter."""
        basicConfig(level=logging.DEBUG)
        show, expected_output_list = self._prepare_show_config()
        recorded_output_list = []
        expected_output_dict = {}
        for key, expected_val in expected_output_list:
            expected_output_dict[key] = expected_val
        self.assertTrue(execute_board_configuration(show, recorded_gui_updates=recorded_output_list))
        for scene_id, filter_id, key, value_str in recorded_output_list:
            self.assertEqual(scene_id, 0, "Expected scene ID to be 0.")
            self.assertTrue(expected_output_dict[filter_id] - 5 < int(value_str) < expected_output_dict[filter_id] + 5,
                            f"Expected configuration of {filter_id} to be {expected_output_dict[filter_id]} but got {value_str} instead.")
