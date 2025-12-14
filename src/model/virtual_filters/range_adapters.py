"""Contains range adapter filters.

EightBitToFloatRange -- ranged 8bit to float.
ColorGlobalBrightnessMixinVFilter -- Global Brightness output.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from model.filter import DataType, Filter, FilterTypeEnumeration, VirtualFilter

if TYPE_CHECKING:
    from model import Scene

logger = getLogger(__name__)


class SixteenBitToFloatRange(VirtualFilter):
    """Converts 16 bit ranges to float."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Instantiate the filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE, pos=pos)

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case "value":
                return f"{self.filter_id}_float_range:value"
        return None

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        filter_: Filter = Filter(
            filter_id=f"{self.filter_id}_16bit_to_float",
            filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT,
            scene=self.scene,
        )
        filter_._initial_parameters = {}
        filter_._filter_configurations = {}
        filter_._in_data_types = {}
        filter_._out_data_types = {}
        filter_._gui_update_keys = {}
        filter_._in_data_types = {}
        filter_._channel_links = {"value_in": self.channel_links["value_in"]}
        filter_list.append(filter_)
        filter_ = Filter(
            filter_id=f"{self.filter_id}_float_range",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE,
            scene=self.scene,
        )
        filter_._initial_parameters = self.initial_parameters
        filter_._filter_configurations = {}
        filter_._in_data_types = {"value_in": DataType.DT_DOUBLE}
        filter_._out_data_types = {"value": DataType.DT_DOUBLE}
        filter_._gui_update_keys = {
            "lower_bound_in": DataType.DT_16_BIT,
            "upper_bound_in": DataType.DT_16_BIT,
            "lower_bound_out": DataType.DT_DOUBLE,
            "upper_bound_out": DataType.DT_DOUBLE,
        }
        filter_._in_data_types = {}
        filter_._channel_links = {"value_in": f"{self.filter_id}_16bit_to_float:value"}
        filter_list.append(filter_)


class EightBitToFloatRange(VirtualFilter):
    """Convert 8-bit ranges into float ranges using a V-Filter."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Convert 8-bit ranges into float ranges using a V-Filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE, pos=pos)

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case "value":
                return f"{self.filter_id}_float_range:value"
        return None

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        filter_: Filter = Filter(
            filter_id=f"{self.filter_id}_8bit_to_float",
            filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT,
            scene=self.scene,
        )
        filter_._initial_parameters = {}
        filter_._filter_configurations = {}
        filter_._in_data_types = {}
        filter_._out_data_types = {}
        filter_._gui_update_keys = {}
        filter_._in_data_types = {}
        filter_._channel_links = {"value_in": self.channel_links["value_in"]}
        filter_list.append(filter_)
        filter_ = Filter(
            filter_id=f"{self.filter_id}_float_range",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE,
            scene=self.scene,
        )
        filter_._initial_parameters = self.initial_parameters
        filter_._filter_configurations = {}
        filter_._in_data_types = {"value_in": DataType.DT_DOUBLE}
        filter_._out_data_types = {"value": DataType.DT_DOUBLE}
        filter_._gui_update_keys = {
            "lower_bound_in": DataType.DT_8_BIT,
            "upper_bound_in": DataType.DT_8_BIT,
            "lower_bound_out": DataType.DT_DOUBLE,
            "upper_bound_out": DataType.DT_DOUBLE,
        }
        filter_._in_data_types = {}
        filter_._channel_links = {"value_in": f"{self.filter_id}_8bit_to_float:value"}
        filter_list.append(filter_)


class DimmerGlobalBrightnessMixinVFilter(VirtualFilter):
    """V-Filter that allows brightness mixin for 8bit and 16bit values."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int, int] | None = None) -> None:
        """Instantiate a new dimmer brightness mixin vfilter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN, pos=pos)
        self._configuration_supported = True
        self._out_data_types["dimmer_out8b"] = DataType.DT_8_BIT
        self._out_data_types["dimmer_out16b"] = DataType.DT_16_BIT
        self._in_data_types["input"] = DataType.DT_16_BIT  # TODO make this configurable
        self._in_data_types["mixin"] = DataType.DT_16_BIT

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        out_16b = self.filter_configurations.get("has_16bit_output") == "true"
        out_8b = self.filter_configurations.get("has_8bit_output") == "true"
        if virtual_port_id == "dimmer_out8b":
            if out_8b and out_16b:
                return f"{self.filter_id}_16b_downsampler:upper"
            if out_8b:
                return f"{self._filter_id}_8b_range:value"
            raise ValueError("Requested 8bit output port but 8bit output is disabled.")
        if virtual_port_id == "dimmer_out16b":
            if out_16b:
                return f"{self._filter_id}_16b_range:value"
            raise ValueError("Requested 8bit output port but 16bit output is disabled.")
        raise ValueError("Unknown output port")

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        out_16b = self.filter_configurations.get("has_16bit_output") == "true"
        out_8b = self.filter_configurations.get("has_8bit_output") == "true"
        needs_8bit_input = self.filter_configurations["input_method"] == "8bit"
        needs_global_brightness_input = self.channel_links.get("mixin") is None
        # TODO place const float 1.0 if mixin port not connected
        # TODO add input global brightness dimmer if input port not connected

        # TODO add 8bit to float range adapter if required
        # TODO add 16bit to float range adapter if required

        # TODO inst mac filter with offset = 0

        if out_16b:
            range16b_out_filter = Filter(
                self.scene,
                f"{self._filter_id}_16b_range",
                FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE,
                pos=self.pos,
                filter_configurations={
                    "lower_bound_in": "0.0",
                    "upper_bound_in": "1.0",
                    "lower_bound_out": "0",
                    "upper_bound_out": "65565",
                    "limit_range": "1"
                }
            )
            # TODO configure input of range16b_out_filter
            filter_list.append(range16b_out_filter)
            if out_8b:
                pass # TODO inst 16bit to 8bit adapter as f"{self.filter_id}_16b_downsampler"
        else:
            range8b_out_filter = Filter(
                self.scene,
                f"{self._filter_id}_8b_range",
                FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_8BIT_RANGE,
                pos=self.pos,
                filter_configurations={
                    "lower_bound_in": "0.0",
                    "upper_bound_in": "1.0",
                    "lower_bound_out": "0",
                    "upper_bound_out": "255",
                    "limit_range": "1"
                }
            )
            # TODO configure input of range8b_out_filter
            filter_list.append(range8b_out_filter)

    @override
    def deserialize(self) -> None:
        if self.filter_configurations.get("has_8bit_output") is None:
            self.filter_configurations["has_8bit_output"] = "true"
        if self.filter_configurations.get("has_16bit_output") is None:
            self.filter_configurations["has_16bit_output"] = "false"
        if self.filter_configurations.get("input_method") is None:
            self.filter_configurations["input_method"] = "16bit"


class ColorGlobalBrightnessMixinVFilter(VirtualFilter):
    """V-Filter that provides the global brightness property."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Instantiate a color global brightness filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN, pos=pos)

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        if virtual_port_id == "out":
            return f"{self.filter_id}_color_recomposition:value"
        raise ValueError("Unknown output port")

    def _instantiate_black_constant(self, filter_list: list[Filter]) -> None:
        logger.warning(
            "Instantiating black constant for brightness mixing %s due to missing color input", self.filter_id
        )
        c = Filter(
            filter_id=f"{self.filter_id}_color_recomposition",
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
            scene=self.scene,
        )
        c.initial_parameters["value"] = "0,0,0"
        filter_list.append(c)

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        if self.channel_links.get("color_in") is None:
            self._instantiate_black_constant(filter_list)
            return
        brightness_input = self.channel_links.get("brightness")
        normalize_from_16bit: bool = False
        if not brightness_input:
            brightness_input = f"{self.filter_id}_global_brightness_input"
            brightness_input_filter = Filter(
                filter_id=brightness_input,
                filter_type=FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS,
                scene=self.scene,
            )
            brightness_input += ":brightness"
            filter_list.append(brightness_input_filter)
            logger.debug("Created global master as input was left empty")
            normalize_from_16bit = True
        conv_filter_id = f"{self.filter_id}__input_converter"
        conv_filter = Filter(
            filter_id=conv_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT
            if normalize_from_16bit
            else FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT,
            pos=self.pos,
            scene=self.scene,
        )
        conv_filter.channel_links["value_in"] = brightness_input
        filter_list.append(conv_filter)
        brightness_input = conv_filter_id + ":value"

        filter_const_zero_id = f"{self.filter_id}_zero_f"
        filter_const_zero = Filter(
            filter_id=filter_const_zero_id,
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            scene=self.scene,
        )
        filter_const_zero.initial_parameters["value"] = "0.0"
        filter_list.append(filter_const_zero)
        filter_const_zero_id += ":value"
        # TODO add normalization and conversion only if input isn't already a float
        filter_const_norm_id = f"{self.filter_id}_norm_f"
        filter_const_norm = Filter(
            filter_id=filter_const_norm_id,
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            scene=self.scene,
        )
        filter_const_norm.initial_parameters["value"] = str(1 / 2**16) if normalize_from_16bit else str(1 / 255)
        filter_list.append(filter_const_norm)
        filter_const_norm_id += ":value"
        brightness_normalization_filter_id = f"{self.filter_id}_brightness_normalization"
        brightness_normalization_filter = Filter(
            filter_id=brightness_normalization_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC,
            scene=self.scene,
        )
        brightness_normalization_filter.channel_links["summand"] = filter_const_zero_id
        brightness_normalization_filter.channel_links["factor2"] = filter_const_norm_id
        brightness_normalization_filter.channel_links["factor1"] = brightness_input
        filter_list.append(brightness_normalization_filter)
        brightness_normalization_filter_id += ":value"

        color_decomposition_filter_id = f"{self.filter_id}_color_decomposition"
        color_decomposition_filter = Filter(
            filter_id=color_decomposition_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT,
            scene=self.scene,
        )
        color_decomposition_filter.channel_links["input"] = self.channel_links["color_in"]
        filter_list.append(color_decomposition_filter)

        brightness_multiplication_filter_id = f"{self.filter_id}_brightness_multiplication"
        brightness_multiplication_filter = Filter(
            filter_id=brightness_multiplication_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC,
            scene=self.scene,
        )
        brightness_multiplication_filter.channel_links["factor1"] = color_decomposition_filter_id + ":i"
        brightness_multiplication_filter.channel_links["factor2"] = brightness_normalization_filter_id
        brightness_multiplication_filter.channel_links["summand"] = filter_const_zero_id
        filter_list.append(brightness_multiplication_filter)
        brightness_multiplication_filter_id += ":value"

        color_recomposition_filter = Filter(
            filter_id=f"{self.filter_id}_color_recomposition",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR,
            scene=self.scene,
        )
        color_recomposition_filter.channel_links["h"] = color_decomposition_filter_id + ":h"
        color_recomposition_filter.channel_links["s"] = color_decomposition_filter_id + ":s"
        color_recomposition_filter.channel_links["i"] = brightness_multiplication_filter_id
        filter_list.append(color_recomposition_filter)
