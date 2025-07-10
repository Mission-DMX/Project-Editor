from model import DataType, Scene
from model.filter import Filter, FilterTypeEnumeration
from model.virtual_filters.auto_tracker_filter import AutoTrackerFilter
from view.show_mode.editor.nodes.base.filternode import FilterNode


class CueListNode(FilterNode):
    """Filter to represent any filter fader"""
    nodeName = "Cues"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_CUES, name=name, terminals={
            "time": {"io": "in"},
            "time_scale": {"io": "in"},
        }, allow_add_output=True)

        try:
            mapping_from_file = model.filter_configurations["mapping"]
            self.filter.filter_configurations["mapping"] = mapping_from_file
            self.parse_and_add_output_channels(mapping_from_file)
        except:
            self.filter.filter_configurations["mapping"] = ""

        try:
            self.filter.filter_configurations["end_handling"] = model.filter_configurations["end_handling"]
        except:
            self.filter.filter_configurations["end_handling"] = ""

        try:
            self.filter.filter_configurations["cuelist"] = model.filter_configurations["cuelist"]
        except:
            self.filter.filter_configurations["cuelist"] = ""

        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.in_data_types["time_scale"] = DataType.DT_DOUBLE
        self.filter.gui_update_keys["run_mode"] = ["play", "pause", "to_next_cue", "stop"]
        self.filter.gui_update_keys["run_cue"] = DataType.DT_16_BIT
        self.filter.gui_update_keys["next_cue"] = DataType.DT_16_BIT
        self.filter.default_values["time_scale"] = "1.0"
        self.channel_hints["time"] = " [ms]"

    def parse_and_add_output_channels(self, mappings: str) -> None:
        output_list = []
        for channel_dev in mappings.split(";"):
            if channel_dev:
                splitted_channel_dev = channel_dev.split(":")
                if len(splitted_channel_dev) > 1:
                    channel_name = splitted_channel_dev[0]
                    channel_type = DataType.from_filter_str(splitted_channel_dev[1])
                    if channel_name not in self.outputs():
                        # TODO also check data type compatibility here
                        self.addOutput(channel_name)
                    output_list.append(channel_name)
                    self.filter.out_data_types[channel_name] = channel_type


class ShiftFilterNode(FilterNode):
    def __init__(self, model: Filter, name: str, id_: int, data_type: DataType) -> None:
        super().__init__(model=model, filter_type=id_, name=name, allow_add_output=True, terminals={
            "input": {"io": "in"},
            "switch_time": {"io": "in"},
            "time": {"io": "in"},
        })

        self.filter.in_data_types["input"] = data_type
        self.filter.in_data_types["switch_time"] = DataType.DT_DOUBLE
        self.filter.in_data_types["time"] = DataType.DT_DOUBLE
        self.filter.default_values["time"] = "0"
        self.filter.default_values["switch_time"] = "1000"
        self.channel_hints["switch_time"] = " [ms]"
        self.channel_hints["time"] = " [ms]"

        try:
            if isinstance(model, Scene):
                # FIXME using the filter type as its ID seams odd
                found_filter = model.get_filter_by_id(str(id_))
                if found_filter:
                    self.filter.filter_configurations["nr_outputs"] = str(
                        int(found_filter.filter_configurations.get("nr_outputs")))
                else:
                    self.filter.filter_configurations["nr_outputs"] = "0"
            else:
                self.filter.filter_configurations["nr_outputs"] = str(
                    int(model.filter_configurations.get("nr_outputs")))
        except ValueError:
            self.filter.filter_configurations["nr_outputs"] = "0"

        self._data_type = data_type
        self.setup_output_terminals()

    def setup_output_terminals(self) -> None:
        existing_output_keys = [k for k in self.outputs()]
        previous_output_count = len(existing_output_keys)
        new_output_count = int(self.filter.filter_configurations["nr_outputs"])
        if previous_output_count > new_output_count:
            for i in range(previous_output_count - new_output_count):
                key_to_drop = existing_output_keys[len(existing_output_keys) - i - 1]
                self.removeTerminal(key_to_drop)
        else:
            for i in range(new_output_count):
                if i >= previous_output_count:
                    channel_name = "output_" + str(i + 1)
                    self.addOutput(channel_name)
                    self.filter.out_data_types[channel_name] = self._data_type

    def update_node_after_settings_changed(self) -> None:
        self.setup_output_terminals()


class Shift8BitNode(ShiftFilterNode):
    nodeName = "filter_shift_8bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_8BIT, DataType.DT_8_BIT)


class Shift16BitNode(ShiftFilterNode):
    nodeName = "filter_shift_16bit"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_16BIT, DataType.DT_16_BIT)


class ShiftFloatNode(ShiftFilterNode):
    nodeName = "filter_shift_float"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_FLOAT, DataType.DT_DOUBLE)


class ShiftColorNode(ShiftFilterNode):
    nodeName = "filter_shift_color"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model, name, FilterTypeEnumeration.FILTER_EFFECT_SHIFT_COLOR, DataType.DT_COLOR)


class AutoTrackerNode(FilterNode):
    nodeName = "AutoTracker"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_AUTOTRACKER, name=name,
                         allow_add_output=True, terminals={})
        self.setup_output_terminals()

    def setup_output_terminals(self) -> None:

        f = self.filter
        if isinstance(f, AutoTrackerFilter):
            trackers = f.number_of_concurrent_trackers + 1
            if trackers < len(self.terminals) / 3:
                self.terminals.clear()
            for i in range(int(len(self.terminals) / 3), trackers, 1):
                min_brightness_filter_id: str = f.get_min_brightness_filter_id()
                self.addOutput(min_brightness_filter_id)
                self.addOutput(f"Tracker{i}_Pan")
                self.addOutput(f"Tracker{i}_Tilt")
                associated_dt = f.get_data_type_of_tracker(i)
                self.filter.out_data_types[f"Tracker{i}_Pan"] = associated_dt
                self.filter.out_data_types[f"Tracker{i}_Tilt"] = associated_dt
                self.filter.out_data_types[min_brightness_filter_id] = DataType.DT_DOUBLE

    def update_node_after_settings_changed(self) -> None:
        self.setup_output_terminals()


class EffectsStackNode(FilterNode):
    nodeName = "EffectsStack"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_EFFECTSSTACK, name=name,
                         allow_add_output=True, terminals={})
        self.setup_output_terminals()

    def setup_output_terminals(self) -> None:
        pass

    def update_node_after_settings_changed(self) -> None:
        super().update_node_after_settings_changed()
        self.setup_output_terminals()
