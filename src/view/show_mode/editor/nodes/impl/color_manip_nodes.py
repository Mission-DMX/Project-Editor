from model.filter import FilterTypeEnumeration, DataType
from view.show_mode.editor.nodes import FilterNode


class ColorMixerNode(FilterNode):
    nodeName = "Color Mixer"
    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_COLOR_MIXER, name=name)
        self.addOutput("value")
        self.filter.out_data_types["value"] = DataType.DT_COLOR
        if not self.filter.filter_configurations.get("input_count"):
            self.filter.filter_configurations["input_count"] = "2"
        self.setup_input_terminals()

    def setup_input_terminals(self):
        required_inputs = set()
        for i in range(int(self.filter.filter_configurations.get("input_count") or "0")):
            required_inputs.add(str(i))
        existing_inputs = set()
        for k in self.inputs().keys():
            existing_inputs.add(k)
        for i in required_inputs - existing_inputs:
            self.addInput(i)
            self.filter.in_data_types[i] = DataType.DT_COLOR
            self.filter.default_values[i] = "0,0,0"
        for i in existing_inputs - required_inputs:
            self.removeTerminal(i)
            self.filter.in_data_types.pop(i)
            self.filter.default_values.pop(i)

    def update_node_after_settings_changed(self):
        self.setup_input_terminals()
