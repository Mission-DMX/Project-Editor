
from model import Scene
from model.filter import VirtualFilter, Filter, DataType, FilterTypeEnumeration


class SixteenBitToFloatRange(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_16BIT_TO_FLOAT_RANGE, pos=pos)

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'value':
                return "{}_float_range:value".format(self.filter_id)
        return None

    def instantiate_filters(self, filter_list: list[Filter]):
        filter = Filter(
            filter_id="{}_16bit_to_float".format(self.filter_id),
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
            filter_id="{}_float_range".format(self.filter_id),
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
        filter._channel_links = {'value_in': "{}_16bit_to_float:value".format(self.filter_id)}
        filter_list.append(filter)


class EightBitToFloatRange(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, pos: tuple[int] | None = None):
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_FILTER_ADAPTER_8BIT_TO_FLOAT_RANGE, pos=pos)

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'value':
                return "{}_float_range:value".format(self.filter_id)
        return None

    def instantiate_filters(self, filter_list: list[Filter]):
        filter = Filter(
            filter_id="{}_8bit_to_float".format(self.filter_id),
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
            filter_id="{}_float_range".format(self.filter_id),
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
        filter._channel_links = {'value_in': "{}_8bit_to_float:value".format(self.filter_id)}
        filter_list.append(filter)
