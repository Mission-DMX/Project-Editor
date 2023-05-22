from model import DataType
from view.show_mode.nodes import FilterNode


class CueListNode(FilterNode):
    """Filter to represent any filter fader"""
    nodeName = "Cues"

    def __init__(self, name):
        super().__init__(filter_type=44, name=name, terminals={
            'time': {'io': 'in'},
            'wash_x_pos': {'io': 'out'},
            'wash_y_pos': {'io': 'out'},
            'wash_dimmer': {'io': 'out'},
            'wash_color': {'io': 'out'}
        })
        self.filter.filter_configurations["mapping"] = ""
        self.filter.filter_configurations["end_handling"] = ""
        self.filter.filter_configurations["cuelist"] = ""

        self._in_value_types["time"] = DataType.DT_DOUBLE
