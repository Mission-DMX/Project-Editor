from model import Scene
from model.filter import VirtualFilter, Filter, DataType


class PanTiltConstantFilter(VirtualFilter):

    def __init__(self, scene: "Scene", filter_id: str, filter_type: int):
        super().__init__(scene, filter_id, filter_type)
        self._pan = 0.5
        self._tilt = 0.5
        self._eight_bit_available = False
        self._sixteen_bit_available = True

        self._filter_configurations = {}
        self._in_data_types = {}
        self._out_data_types = {'pan_8bit': DataType.DT_8_BIT,
                                'tilt_8bit': DataType.DT_8_BIT,
                                'pan_16bit': DataType.DT_16_BIT,
                                'tilt_16bit': DataType.DT_16_BIT
                                }
        self._gui_update_keys = {'pan': DataType.DT_DOUBLE,
                                 'tilt': DataType.DT_DOUBLE
                                 }

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        match virtual_port_id:
            case 'pan_8bit':
                return "{}_8bit_pan".format(self.filter_id)
            case 'tilt_8bit':
                return "{}_8bit_tilt".format(self.filter_id)
            case 'pan_16bit':
                return "{}_16bit_pan".format(self.filter_id)
            case 'tilt_16bit':
                return "{}_16bit_tilt".format(self.filter_id)
        return "error"

    def instantiate_filters(self, filter_list: list[Filter]):
        if self._eight_bit_available:
            self.instanitate_specific_filter(filter_list, DataType.DT_8_BIT, False)
            self.instanitate_specific_filter(filter_list, DataType.DT_8_BIT, True)
        if self._sixteen_bit_available:
            self.instanitate_specific_filter(filter_list, DataType.DT_16_BIT, False)
            self.instanitate_specific_filter(filter_list, DataType.DT_16_BIT, True)

    def instanitate_specific_filter(self, filter_list: list[Filter], datatype: DataType, tilt: bool):
        filter = Filter(
            filter_id="{}_{}bit_{}".format(self.filter_id, '16' if datatype == DataType.DT_16_BIT else '8',
                                           'tilt' if tilt else 'pan'),
            filter_type=1 if datatype == DataType.DT_16_BIT else 0,
            scene=self.scene
        )
        filter._initial_parameters = {'value': str(int(self.tilt * (65535 if datatype == DataType.DT_16_BIT else 255)))}
        filter._filter_configurations = {}
        filter._in_data_types = {}
        filter._out_data_types = {'value': datatype}
        filter._gui_update_keys = {'value': datatype}
        filter._in_data_types = {}
        filter._channel_links = {}
        filter_list.append(filter)

    @property
    def pan(self):
        return self._pan

    @pan.setter
    def pan(self, pan):
        self._pan = pan

    @property
    def tilt(self):
        return self._tilt

    @tilt.setter
    def tilt(self, tilt):
        self._tilt = tilt

    @property
    def sixteen_bit_available(self):
        return self._sixteen_bit_available

    @sixteen_bit_available.setter
    def sixteen_bit_available(self, _sixteen_bit_available: bool):
        self._sixteen_bit_available = _sixteen_bit_available

    @property
    def eight_bit_available(self):
        return self._eight_bit_available

    @eight_bit_available.setter
    def eight_bit_available(self, _eight_bit_available: bool):
        self._eight_bit_available = _eight_bit_available
