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
            self.filter.initial_parameters["mapping"] = model.initial_parameters["mapping"]
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

