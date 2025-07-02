# coding=utf-8
from logging import getLogger

from model import Scene
from model.filter import DataType, Filter, FilterTypeEnumeration, VirtualFilter

logger = getLogger(__file__)


class SixteenBitToFloatRange(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE, pos=pos)

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'value':
                return f"{self.filter_id}_float_range:value"
        return None

    def instantiate_filters(self, filter_list: list[Filter]):
        filter = Filter(
            filter_id=f"{self.filter_id}_16bit_to_float",
            filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT,
            scene=self.scene
        )
        filter._initial_parameters = {}
        filter._filter_configurations = {}
        filter._in_data_types = {}
        filter._out_data_types = {}
        filter._gui_update_keys = {}
        filter._in_data_types = {}
        filter._channel_links = {'value_in': self.channel_links['value_in']}
        filter_list.append(filter)
        filter = Filter(
            filter_id=f"{self.filter_id}_float_range",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE,
            scene=self.scene
        )
        filter._initial_parameters = self.initial_parameters
        filter._filter_configurations = {}
        filter._in_data_types = {'value_in': DataType.DT_DOUBLE}
        filter._out_data_types = {'value': DataType.DT_DOUBLE}
        filter._gui_update_keys = {'lower_bound_in': DataType.DT_16_BIT,
                                   'upper_bound_in': DataType.DT_16_BIT,
                                   'lower_bound_out': DataType.DT_DOUBLE,
                                   'upper_bound_out': DataType.DT_DOUBLE}
        filter._in_data_types = {}
        filter._channel_links = {'value_in': f"{self.filter_id}_16bit_to_float:value"}
        filter_list.append(filter)


class EightBitToFloatRange(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE, pos=pos)

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'value':
                return f"{self.filter_id}_float_range:value"
        return None

    def instantiate_filters(self, filter_list: list[Filter]):
        filter = Filter(
            filter_id=f"{self.filter_id}_8bit_to_float",
            filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT,
            scene=self.scene
        )
        filter._initial_parameters = {}
        filter._filter_configurations = {}
        filter._in_data_types = {}
        filter._out_data_types = {}
        filter._gui_update_keys = {}
        filter._in_data_types = {}
        filter._channel_links = {'value_in': self.channel_links['value_in']}
        filter_list.append(filter)
        filter = Filter(
            filter_id=f"{self.filter_id}_float_range",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE,
            scene=self.scene
        )
        filter._initial_parameters = self.initial_parameters
        filter._filter_configurations = {}
        filter._in_data_types = {'value_in': DataType.DT_DOUBLE}
        filter._out_data_types = {'value': DataType.DT_DOUBLE}
        filter._gui_update_keys = {'lower_bound_in': DataType.DT_8_BIT,
                                   'upper_bound_in': DataType.DT_8_BIT,
                                   'lower_bound_out': DataType.DT_DOUBLE,
                                   'upper_bound_out': DataType.DT_DOUBLE}
        filter._in_data_types = {}
        filter._channel_links = {'value_in': f"{self.filter_id}_8bit_to_float:value"}
        filter_list.append(filter)


class ColorGlobalBrightnessMixinVFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLOR_GLOBAL_BRIGHTNESS_MIXIN, pos=pos)

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        if virtual_port_id == "out":
            return f"{self.filter_id}_color_recomposition:value"
        raise ValueError("Unknown output port")

    def instantiate_filters(self, filter_list: list[Filter]):
        brightness_input = self.channel_links.get('brightness')
        normalize_from_16bit: bool = False
        if not brightness_input:
            brightness_input = f"{self.filter_id}_global_brightness_input"
            brightness_input_filter = Filter(
                filter_id=brightness_input,
                filter_type=FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS,
                scene=self.scene
            )
            brightness_input += ":brightness"
            filter_list.append(brightness_input_filter)
            logger.debug("Created global master as input was left empty")
            normalize_from_16bit = True
        conv_filter_id = f"{self.filter_id}__input_converter"
        conv_filter = Filter(filter_id=conv_filter_id,
                             filter_type=FilterTypeEnumeration.FILTER_TYPE_ADAPTER_16BIT_TO_FLOAT
                             if normalize_from_16bit else FilterTypeEnumeration.FILTER_TYPE_ADAPTER_8BIT_TO_FLOAT,
                             pos=self.pos,
                             scene=self.scene)
        conv_filter.channel_links['value_in'] = brightness_input
        filter_list.append(conv_filter)
        brightness_input = conv_filter_id + ":value"

        filter_const_zero_id = f"{self.filter_id}_zero_f"
        filter_const_zero = Filter(
            filter_id=filter_const_zero_id,
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            scene=self.scene
        )
        filter_const_zero.initial_parameters['value'] = '0.0'
        filter_list.append(filter_const_zero)
        filter_const_zero_id += ":value"
        # TODO add normalization and conversion only if input isn't already a float
        filter_const_norm_id = f"{self.filter_id}_norm_f"
        filter_const_norm = Filter(
            filter_id=filter_const_norm_id,
            filter_type=FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
            scene=self.scene
        )
        filter_const_norm.initial_parameters['value'] = str(1 / 2 ** 16) if normalize_from_16bit else str(1 / 255)
        filter_list.append(filter_const_norm)
        filter_const_norm_id += ":value"
        brightness_normalization_filter_id = f"{self.filter_id}_brightness_normalization"
        brightness_normalization_filter = Filter(
            filter_id=brightness_normalization_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC,
            scene=self.scene
        )
        brightness_normalization_filter.channel_links['summand'] = filter_const_zero_id
        brightness_normalization_filter.channel_links['factor2'] = filter_const_norm_id
        brightness_normalization_filter.channel_links['factor1'] = brightness_input
        filter_list.append(brightness_normalization_filter)
        brightness_normalization_filter_id += ":value"

        color_decomposition_filter_id = f"{self.filter_id}_color_decomposition"
        color_decomposition_filter = Filter(
            filter_id=color_decomposition_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_FLOAT,
            scene=self.scene
        )
        color_decomposition_filter.channel_links['input'] = self.channel_links['color_in']
        filter_list.append(color_decomposition_filter)

        brightness_multiplication_filter_id = f"{self.filter_id}_brightness_multiplication"
        brightness_multiplication_filter = Filter(
            filter_id=brightness_multiplication_filter_id,
            filter_type=FilterTypeEnumeration.FILTER_ARITHMETICS_MAC,
            scene=self.scene
        )
        brightness_multiplication_filter.channel_links['factor1'] = color_decomposition_filter_id + ":i"
        brightness_multiplication_filter.channel_links['factor2'] = brightness_normalization_filter_id
        brightness_multiplication_filter.channel_links['summand'] = filter_const_zero_id
        filter_list.append(brightness_multiplication_filter)
        brightness_multiplication_filter_id += ":value"

        color_recomposition_filter = Filter(
            filter_id=f"{self.filter_id}_color_recomposition",
            filter_type=FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR,
            scene=self.scene
        )
        color_recomposition_filter.channel_links['h'] = color_decomposition_filter_id + ':h'
        color_recomposition_filter.channel_links['s'] = color_decomposition_filter_id + ':s'
        color_recomposition_filter.channel_links['i'] = brightness_multiplication_filter_id
        filter_list.append(color_recomposition_filter)
