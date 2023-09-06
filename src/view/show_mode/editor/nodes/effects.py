from model import DataType
from model.broadcaster import Broadcaster
from .filternode import FilterNode


class CueListNode(FilterNode):
    """Filter to represent any filter fader"""
    nodeName = "Cues"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=44, name=name, terminals={
            'time': {'io': 'in'}
        }, allowAddOutput=True)

        try:
            mapping_from_file = model.initial_parameters["mapping"]
            self.filter.initial_parameters["mapping"] = mapping_from_file
            self.parse_and_add_output_channels(mapping_from_file)
        except:
            self.filter.initial_parameters["mapping"] = ""

        try:
            self.filter.initial_parameters["end_handling"] = model.initial_parameters["end_handling"]
        except:
            self.filter.initial_parameters["end_handling"] = ""

        try:
            self.filter.initial_parameters["cuelist"] = model.initial_parameters["cuelist"]
        except:
            self.filter.initial_parameters["cuelist"] = ""

        self.filter.in_data_types["time"] = DataType.DT_DOUBLE

    def parse_and_add_output_channels(self, mappings: str):
        for channel_dev in mappings.split(';'):
            if channel_dev:
                splitted_channel_dev = channel_dev.split(':')
                if len(splitted_channel_dev) > 1:
                    channel_name = splitted_channel_dev[0]
                    channel_type = DataType.from_filter_str(splitted_channel_dev[1])
                    self.addOutput(channel_name)
                    self.filter.out_data_types[channel_name] = channel_type


class ShiftFilterNode(FilterNode):
    def __init__(self, model, name, id: int, data_type: DataType):
        super().__init__(model=model, filter_type=id, name=name, allowAddOutput=True, terminals={
            'input': {'io': 'in'},
            'switch_time': {'io': 'in'},
            'time': {'io': 'in'}
        }, )

        self.filter.in_data_types["input"] = data_type
        self.filter.in_data_types["switch_time"] = DataType.DT_DOUBLE
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE

        try:
            print(dir(model))
            self.filter.filter_configurations["nr_outputs"] = str(int(model.filter_configurations.get("nr_outputs")))
        except ValueError:
            self.filter.filter_configurations["nr_outputs"] = "0"

        for i in range(int(self.filter.filter_configurations["nr_outputs"])):
            channel_name = "output_" + str(i + 1)
            self.addOutput(channel_name)
            self.filter.out_data_types[channel_name] = data_type


class Shift8BitNode(ShiftFilterNode):
    nodeName = "filter_shift_8bit"

    def __init__(self, model, name):
        super().__init__(model, name, 45, DataType.DT_8_BIT)


class Shift16BitNode(ShiftFilterNode):
    nodeName = "filter_shift_16bit"

    def __init__(self, model, name):
        super().__init__(model, name, 46, DataType.DT_16_BIT)


class ShiftFloatNode(ShiftFilterNode):
    nodeName = "filter_shift_float"

    def __init__(self, model, name):
        super().__init__(model, name, 47, DataType.DT_DOUBLE)


class ShiftColorNode(ShiftFilterNode):
    nodeName = "filter_shift_color"

    def __init__(self, model, name):
        super().__init__(model, name, 48, DataType.DT_COLOR)
