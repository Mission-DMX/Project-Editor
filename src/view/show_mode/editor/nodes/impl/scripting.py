from model import DataType
from model.filter import Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class ConfigurationError(Exception):
    pass


_default_script = """

function update()
    -- This method will be called once per DMX output cycle
    -- Put your effect here
end

function scene_activated()
    -- This method will be called every time the show is switched to this scene
end

"""


class LuaFilterNode(FilterNode):
    nodeName = "Lua"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA, name=name,
                         allow_add_output=True, terminals={})
        self._setup_terminals()

    def update_node_after_settings_changed(self) -> None:
        self._setup_terminals()

    def _setup_terminals(self) -> None:
        self._ensure_parameters()
        legal_inputs: list[str] = []
        for input_mapping in self.filter.filter_configurations["in_mapping"].split(";"):
            if not input_mapping:
                continue
            channel_name, data_type = input_mapping.split(":")
            if channel_name in legal_inputs:
                raise ConfigurationError("Connection key already in use")
            if channel_name not in self.terminals:
                self.addInput(name=channel_name)
            self.filter.in_data_types[channel_name] = DataType.from_filter_str(data_type)
            legal_inputs.append(channel_name)
        for output_mapping in self.filter.filter_configurations["out_mapping"].split(";"):
            if not output_mapping:
                continue
            channel_name, data_type = output_mapping.split(":")
            if channel_name in legal_inputs:
                raise ConfigurationError("Connection key already in use")
            if channel_name not in self.terminals:
                self.addOutput(name=channel_name)
            self.filter.out_data_types[channel_name] = DataType.from_filter_str(data_type)
            legal_inputs.append(channel_name)

        terms_to_remove = [term for term in self.terminals if term not in legal_inputs]
        for term in terms_to_remove:
            self.removeTerminal(term)
            try:
                self.filter.in_data_types.pop(term)
            except KeyError:
                pass
            try:
                self.filter.out_data_types.pop(term)
            except KeyError:
                pass

    def _ensure_parameters(self) -> None:
        if not self.filter.filter_configurations.get("in_mapping"):
            self.filter.filter_configurations["in_mapping"] = ""
        if not self.filter.filter_configurations.get("out_mapping"):
            self.filter.filter_configurations["out_mapping"] = ""
        if not self.filter.initial_parameters.get("script"):
            self.filter.initial_parameters["script"] = _default_script
