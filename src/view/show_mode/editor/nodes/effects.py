from model import DataType
from model.broadcaster import Broadcaster
from .filternode import FilterNode


class CueListNode(FilterNode):
    """Filter to represent any filter fader"""
    nodeName = "Cues"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=44, name=name, terminals={
            'time': {'io': 'in'}},
                         allowAddOutput=True)

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

    # TODO implement shift effect nodes
