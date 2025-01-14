from model.filter import FilterTypeEnumeration, Filter, DataType
from view.show_mode.editor.nodes import FilterNode


class ImportNode(FilterNode):

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_IMPORT, name=name,
                         terminals={}, allowAddOutput=True)
        self.update_node_ports()

    def update_node_ports(self):
        if self.filter is not None:
            target_filter = self.filter.scene.get_filter_by_id(self.filter.filter_configurations.get("target"))
            if isinstance(target_filter, Filter):
                target_ports: set[tuple[str, DataType]] = set()
                current_ports: set[tuple[str, DataType]] = set()
                for port_name in self.outputs():
                    current_ports.add((port_name, target_filter.out_data_types.get(port_name)))
                for port_name, port_dt in target_filter.out_data_types.items():
                    target_ports.add((port_name, port_dt))
                for port_name_to_remove, _ in current_ports - target_ports:
                    self.removeTerminal(port_name_to_remove)
                    self.filter.out_data_types.pop(port_name_to_remove)
                for port_name_to_add, port_dt_to_add in target_ports - current_ports:
                    self.addOutput(port_dt_to_add)
                    self.filter.out_data_types[port_name_to_add] = port_dt_to_add

    def update_node_after_settings_changed(self):
        self.update_node_ports()
