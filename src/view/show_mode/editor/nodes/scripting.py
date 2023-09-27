from model import Filter, DataType
from view.show_mode.editor.nodes import FilterNode


class ConfigurationError(Exception):
    pass


class LuaFilterNode(FilterNode):

    nodeName = 'Lua'

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=50, name=name, allowAddOutput=True, terminals={})
        self._setup_terminals()

    def update_node_after_settings_changed(self):
        self._setup_terminals()

    def _setup_terminals(self):
        legal_inputs: list[str] = []
        for input_mapping in self.filter_configurations['in_mapping'].split(';'):
            channel_name, data_type = input_mapping.split(':')
            if channel_name in legal_inputs:
                raise ConfigurationError("Connection key already in use")
            if channel_name not in self.terminals.keys():
                self.addInput(name=channel_name, io='in')
            self.filter.in_data_types[channel_name] = DataType.from_filter_str(data_type)
            legal_inputs.append(channel_name)
        for output_mapping in self.filter_configurations['out_mapping'].split(';'):
            channel_name, data_type = output_mapping.split(':')
            if channel_name in legal_inputs:
                raise ConfigurationError("Connection key already in use")
            if channel_name not in self.terminals.keys():
                self.addInput(name=channel_name, io='out')
            self.filter.out_data_types[channel_name] = DataType.from_filter_str(data_type)
            legal_inputs.append(channel_name)
        for term in self.terminals.keys():
            if term not in legal_inputs:
                self.removeTerminal(term)
                self.filter.in_data_types.pop(term)
                self.filter.out_data_types.pop(term)
