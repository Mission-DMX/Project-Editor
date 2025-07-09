from model.filter import DataType, Filter, FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class ImportNode(FilterNode):
    node_name = "Filter Import"

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_IMPORT, name=name,
                         terminals={}, allowAddOutput=True)
        self.update_node_ports()

    def update_node_ports(self) -> None:
        if self.filter is not None:
            target_filter = self.filter.scene.get_filter_by_id(self.filter.filter_configurations.get("target"))
            if isinstance(target_filter, Filter):
                target_ports: set[tuple[str, DataType]] = set()
                current_ports: set[tuple[str, DataType]] = set()
                rename_dict: dict[str, str] = {}
                rename_data = self.filter.filter_configurations.get("rename_dict")
                if rename_data:
                    for item in rename_data.split(","):
                        if "=" not in item:
                            continue
                        k, v = item.split("=")
                        rename_dict[k] = v
                for port_name in self.outputs():
                    current_ports.add((port_name, target_filter.out_data_types.get(port_name)))
                for port_name, port_dt in target_filter.out_data_types.items():
                    new_name = rename_dict.get(port_name)
                    if new_name is None:
                        new_name = port_name
                    if new_name == "":
                        continue
                    target_ports.add((new_name, port_dt))
                for port_name_to_remove, _ in current_ports - target_ports:
                    self.removeTerminal(port_name_to_remove)
                    self.filter.out_data_types.pop(port_name_to_remove)
                for port_name_to_add, port_dt_to_add in target_ports - current_ports:
                    self.addOutput(port_name_to_add)
                    self.filter.out_data_types[port_name_to_add] = port_dt_to_add

    def update_node_after_settings_changed(self) -> None:
        self.update_node_ports()
