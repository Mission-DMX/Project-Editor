from model import DataType, Filter
from view.show_mode.editor.nodes import FilterNode


class AggregatingFilterNode(FilterNode):
    """
    This filter node class provides a template for nodes with a variable number of inputs that will be aggregated to a
    single output.
    """

    def __init__(self, target_dt: DataType, model: Filter, name: str, filter_type: int) -> None:
        super().__init__(model=model, filter_type=filter_type, name=name)
        self.addOutput("value")
        self.filter.out_data_types["value"] = target_dt
        if not self.filter.filter_configurations.get("input_count"):
            self.filter.filter_configurations["input_count"] = "2"
        self._data_type = target_dt
        self.setup_input_terminals()

    def setup_input_terminals(self) -> None:
        required_inputs = set()
        try:
            requested_input_count = int(self.filter.filter_configurations.get("input_count") or "0")
        except ValueError:
            requested_input_count = 0
            self.filter.filter_configurations["input_count"] = "0"
        for i in range(requested_input_count):
            required_inputs.add(str(i))
        existing_inputs = set()
        for k in self.inputs():
            existing_inputs.add(k)
        for i in required_inputs - existing_inputs:
            self.addInput(i)
            self.filter.in_data_types[i] = self._data_type
            match self._data_type:
                case DataType.DT_8_BIT:
                    self.filter.default_values[i] = "0"
                case DataType.DT_16_BIT:
                    self.filter.default_values[i] = "0"
                case DataType.DT_DOUBLE:
                    self.filter.default_values[i] = "0.0"
                case DataType.DT_COLOR:
                    self.filter.default_values[i] = "0,0,0"
                case DataType.DT_BOOL:
                    self.filter.default_values[i] = "0"
        for i in existing_inputs - required_inputs:
            self.removeTerminal(i)
            self.filter.in_data_types.pop(i)
            self.filter.default_values.pop(i)

    def update_node_after_settings_changed(self) -> None:
        self.setup_input_terminals()
