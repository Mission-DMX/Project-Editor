"""Color Director vFilter."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import Signal

from controller.network import NetworkManager
from model import DataType, Filter
from model.color_hsi import ColorHSI
from model.filter import FilterTypeEnumeration, VirtualFilter
from model.filter_data.cues.cue import Cue, KeyFrame, StateColor
from model.filter_data.cues.cue_filter_model import CueFilterModel
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.cue_vfilter import CueFilter

if TYPE_CHECKING:
    import proto.FilterMode_pb2
    from model.scene import Scene


class ColorPreset:
    """A color preset.

    Contains all color steps with their fade in time (steps), transfer function and accent colors.

    """

    def __init__(self, filter_str: str = "") -> None:
        """Initialize a color preset.

        Args:
            filter_str: Filter string representation to deserialize. An empty string will initialize an empty preset.

        """
        self.colors: list[tuple[int, TransferFunction, list[ColorHSI]]] = []
        if len(filter_str) > 0:
            for step_str in filter_str.split("#"):
                duration, transf, colors = step_str.split("|")
                duration = int(duration)
                transf = TransferFunction(transf)
                colors = [ColorHSI.from_filter_str(part) for part in colors.split("@")]
                self.colors.append((duration, transf, colors))

    def get_button_visualization(self) -> list[ColorHSI]:
        """Get the representation sequence for highlighting purposes in buttons.

        Returns:
            The first accent color of each step.

        """
        return [t[2][0] for t in self.colors]

    def serialize(self) -> str:
        """Serialize the preset to a string."""
        parts: list[str] = []
        for duration, transfer_function, colors in self.colors:
            parts.append(f"{duration}|{transfer_function.value}|{"@".join(c.format_for_filter() for c in colors)}")
        return "#".join(parts)


def _sanitize_channel_name(name: str) -> str:
    return (name.replace(":", "").replace("#", "").replace("|", "").
            replace("__", "-").replace(" ", "_").strip())


class ColordirectorVFilter(VirtualFilter):
    """VFilter to provide selectable colors.

    A Color Director is a filter that provides color values to defined color groups.
    Color sequences and accent colors can be defined. Accent colors will be evenly distributed into the channels of
    each color group.

    Saved recalls can set color selections based on the stored settings.

    Internally cue filters are used for each color group and presets are cues within them.
    Accent colors are distributed using the formula `SubOut[i] = accent colors[i mod #accent colors]`.
    If the apply all buttons of the UI widget are pressed, the state will be applied to all cues.
    Fade-in curves are stored with the new steps per second time reference.

    """

    configuration_changed = Signal()

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Initializes the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLORDIRECTOR, pos=pos)
        self._color_groups: dict[str, list[str]] = {}
        self._presets: list[ColorPreset] = []
        self._recalls: list[list[int]] = []
        self.in_data_types["time"] = DataType.DT_DOUBLE
        self._in_data_types["time_scale"] = DataType.DT_DOUBLE
        self._registered_callbacks: list[tuple[int, str]] = []
        self._current_active_colors: list[int] = []
        self._cue_filter_to_group_index_mapping: dict[str, int] = {}

    @property
    def presets(self) -> list[ColorPreset]:
        """Returns the list of color presets."""
        return self._presets

    @presets.setter
    def presets(self, presets: list[ColorPreset]) -> None:
        self._presets = presets

    @property
    def output_groups(self) -> dict[str, list[str]]:
        """Get the color output group dictionary."""
        return self._color_groups

    @property
    def recalls(self) -> list[list[int]]:
        """Returns the list of setting recalls."""
        return self._recalls

    def get_ambient_color_count(self) -> int:
        """Get the maximum number of ambient colors in presets."""
        maximum = 0
        for preset in self.presets:
            for _, _, colors in preset.colors:
                maximum = max(maximum, len(colors))
        return maximum

    def _deserialize_color_groups(self) -> None:
        self._color_groups.clear()
        color_group_def = self.filter_configurations.get("colorgroups", "")
        if len(color_group_def) == 0:
            return
        self.out_data_types.clear()
        for group_def in color_group_def.split("#"):
            output_channels = group_def.split("|")
            if len(output_channels) < 1:
                raise ValueError("A least a name of the color group must be defined.")
            name = output_channels[0]
            output_channels.pop(0)
            self._color_groups[name] = output_channels
            for chan_name in output_channels:
                self.out_data_types[chan_name] = DataType.DT_COLOR

    def _serialize_color_groups(self) -> None:
        self.filter_configurations["colorgroups"] = "#".join(f"{_sanitize_channel_name(name)}|{
            "|".join(_sanitize_channel_name(c) for c in channels)}" for name, channels in self._color_groups.items())

    def _deserialize_presets(self) -> None:
        self._presets.clear()
        presets_def = self.filter_configurations.get("presets", "")
        if len(presets_def) == 0:
            return
        self._presets.extend(ColorPreset(p_str) for p_str in presets_def.split("$"))

    def _serialize_presets(self) -> None:
        self._filter_configurations["presets"] = "$".join(c.serialize() for c in self._presets)

    def _serialize_recalls(self) -> None:
        self.filter_configurations["recalls"] = (
            ";".join(",".join(str(state) for state in states) for states in self._recalls))

    def _deserialize_recalls(self) -> None:
        self._recalls.clear()
        recalls_def = self.filter_configurations.get("recalls", "")
        if len(recalls_def) == 0:
            return
        for recall_def in recalls_def.split(";"):
            if len(recall_def) == 0:
                continue
            recall = []
            for state in recall_def.split(","):
                if len(state) == 0:
                    continue
                recall.append(int(state))
            self._recalls.append(recall)

    def populate_presets_with_initial_data(self, short: bool) -> None:
        """Populate the color presets with common initial data.

        This method will generate color presets for the most common color choices.
        The default fade-in is linear with a fade-in time of three seconds.

        Args:
            short: If set to true, a smaller preset field will be generated.

        """
        steps_per_second: int = int(1000 / 40)
        three_secs: int = steps_per_second * 3

        white = ColorPreset()
        white.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(0, 0, 1)]))
        self._presets.append(white)

        if short:
            pink = ColorPreset()
            pink.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(296.0, 0.89, 1)]))
            self._presets.append(pink)
            red = ColorPreset()
            red.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(360.0, 1, 1)]))
            self._presets.append(red)
            orange = ColorPreset()
            orange.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(25, 1, 1)]))
            self._presets.append(orange)
            yellow = ColorPreset()
            yellow.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(60.0, 1, 1)]))
            self._presets.append(yellow)
            green = ColorPreset()
            green.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(114.0, 1, 1)]))
            self._presets.append(green)
            cyan = ColorPreset()
            cyan.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(170.0, 1, 1)]))
            self._presets.append(cyan)
            blue = ColorPreset()
            blue.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(227, 1, 1)]))
            self._presets.append(blue)
            purple = ColorPreset()
            purple.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(265.0, 1, 1)]))
            self._presets.append(purple)
        else:
            for hue in range(0, 360, 18):
                color = ColorPreset()
                color.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(hue, 1, 1)]))
                self._presets.append(color)

    def get_outputs(self) -> list[str]:
        """Get the outputs of this filter."""
        output_list = []
        for group, sub_outs in self._color_groups.items():
            output_list.extend([f"{group}__{output}" for output in sub_outs])
        output_list.sort()
        return output_list

    @override
    def serialize(self) -> None:
        super().serialize()
        self._serialize_color_groups()
        self._serialize_presets()
        self._serialize_recalls()

    @override
    def deserialize(self) -> None:
        super().deserialize()
        self._deserialize_color_groups()
        self._deserialize_presets()
        self._deserialize_recalls()

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        color_group_name, group_output_channel = virtual_port_id.split("__")
        if color_group_name not in self._color_groups:
            return None
        color_group = self._color_groups[color_group_name]
        if group_output_channel not in color_group:
            return None
        return f"{self.filter_id}__cue__{color_group_name}:{group_output_channel}"

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        for callback in self._registered_callbacks:
            self.scene.board_configuration.clear_filter_update_callbacks(callback[0], callback[1])
        self._registered_callbacks.clear()
        self._current_active_colors.clear()
        self._cue_filter_to_group_index_mapping.clear()
        timescale_input = self.channel_links.get("time_scale")
        if timescale_input is None:
            float_const = Filter(self.scene, f"{self.filter_id}__timescale_const",
                                 FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, pos=self.pos,
                                 initial_parameters={"value": "1.0"})
            timescale_input = float_const.filter_id + ":value"
            filter_list.append(float_const)
        time_input = self.channel_links.get("time")
        if time_input is None:
            time_filter = Filter(self.scene, f"{self.filter_id}__time",
                                 FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT, pos=self.pos)
            time_input = time_filter.filter_id + ":value"
            filter_list.append(time_filter)
        for group_index, item in enumerate(self._color_groups.items()):
            color_group_name, output_channels = item
            cue_filter = CueFilter(self.scene,
                                   f"{self.filter_id}__cue__{_sanitize_channel_name(color_group_name)}",
                                   pos=self.pos)
            cue_filter.channel_links["time"] = time_input
            cue_filter.channel_links["time_scale"] = timescale_input
            cfm = CueFilterModel()
            for channel_name in output_channels:
                cfm.add_channel(channel_name, DataType.DT_COLOR)
            for preset in self._presets:
                cue = Cue()
                cfm.append_cue(cue)
                last_time: float = 0
                for fadein_time, transfer_function, colors in preset.colors:
                    kf = KeyFrame(cue)
                    last_time += fadein_time * 40
                    kf.timestamp = last_time / 1000.0
                    for i in range(len(output_channels)):
                        state = StateColor(transfer_function.value)
                        state.color = colors[i % len(colors)]
                        kf.append_state(state)
                    cue.insert_frame(kf)
            if len(self._presets) > 0:
                cfm.default_cue = 0
            cue_filter.filter_configurations.update(cfm.get_as_configuration())
            cue_filter.instantiate_filters(filter_list)
            self.scene.board_configuration.register_filter_update_callback(
                self.scene.scene_id,
                cue_filter.filter_id,
                self._update_active_colors_from_filters
            )
            self._registered_callbacks.append((self.scene.scene_id, cue_filter.filter_id))
            self._cue_filter_to_group_index_mapping[cue_filter.filter_id] = group_index

    @override
    def handle_filter_message(self, key: str, value: str) -> bool:
        match key:
            case "save-selection-to-recall":
                try:
                    target_recall = int(value)
                except ValueError:
                    return False
                if target_recall < 0:
                    return False
                if target_recall >= len(self._recalls):
                    self._recalls.append([])
                    selected_recall = self._recalls[-1]
                else:
                    selected_recall = self._recalls[target_recall]
                current_colors = self.get_current_active_colors()
                if len(current_colors) == 0:
                    return False
                selected_recall.clear()
                selected_recall.extend(current_colors)
                return True
            case "recall":
                try:
                    target_recall = int(value)
                except ValueError:
                    return False
                try:
                    recall = self._recalls[target_recall]
                except IndexError:
                    return False
                nm = NetworkManager()
                for i, group_name in enumerate(self._color_groups.keys()):
                    filter_id, value = self.get_update_msg_for_group_preset_change(group_name, recall[i])
                    filter_id, msg_key = filter_id.split(":")
                    nm.send_gui_update_to_fish(self.scene.scene_id, filter_id, msg_key, value, enque=True)
                return True
            case "call":
                try:
                    group_name, color_preset_index = value.split(",")
                    color_preset_index = int(color_preset_index)
                except ValueError:
                    return False
                nm = NetworkManager()
                filter_id, value = self.get_update_msg_for_group_preset_change(group_name, color_preset_index)
                filter_id, msg_key = filter_id.split(":")
                nm.send_gui_update_to_fish(self.scene.scene_id, filter_id, msg_key, value, enque=True)
                return True
            case "call-column":
                try:
                    color_preset_index = int(value)
                except ValueError:
                    return False
                nm = NetworkManager()
                for group_name in self._color_groups:
                    filter_id, value = self.get_update_msg_for_group_preset_change(group_name, color_preset_index)
                    filter_id, msg_key = filter_id.split(":")
                    nm.send_gui_update_to_fish(self.scene.scene_id, filter_id, msg_key, value, enque=True)
                return True
            case _:
                return False
        return True

    def _update_active_colors_from_filters(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        group_index = self._cue_filter_to_group_index_mapping[param.filter_id]
        self._current_active_colors[group_index] = int(param.parameter_value.split(";")[1])
        self.configuration_changed.emit()

    def get_current_active_colors(self) -> list[int]:
        """Get the current active color presets.

        Returns:
            A list of indexes or an empty list if the filter was not applied and did not receive updates.

        """
        return self._current_active_colors

    def get_update_msg_for_group_preset_change(self, color_group_name: str, preset_index: int) -> tuple[str, str]:
        """Generate message to set the color group value to the given preset.

        Args:
            color_group_name: The key of the group to update.
            preset_index: The index of the preset to use.

        Returns:
            A tuple containing the [target filter ID]:[update key] and update value.

        """
        return f"{self.filter_id}__cue__{_sanitize_channel_name(color_group_name)}:run_cue", str(preset_index)
