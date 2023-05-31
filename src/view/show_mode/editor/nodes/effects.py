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
        self.filter.filter_configurations["mapping"] = ""
        self.filter.filter_configurations["end_handling"] = ""
        self.filter.filter_configurations["cuelist"] = ""

        self.filter.in_data_types["time"] = DataType.DT_DOUBLE

