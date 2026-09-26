"""Color Director vFilter."""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QObject, Signal

from controller.network import NetworkManager
from model import DataType, Filter
from model.color_hsi import ColorHSI
from model.filter import FilterTypeEnumeration, VirtualFilter
from model.filter_data.cues.cue import Cue, EndAction, KeyFrame, StateColor
from model.filter_data.cues.cue_filter_model import CueFilterModel
from model.filter_data.transfer_function import TransferFunction
from model.media_assets.image import AbstractImageAsset
from model.media_assets.registry import get_asset_by_uuid
from model.virtual_filters.cue_vfilter import CueFilter

if TYPE_CHECKING:
    import proto.FilterMode_pb2
    from model.scene import Scene


logger = getLogger(__name__)


_PRESET_DELIMITER = "$"
"""Delimiter separating the serialized color presets within the presets configuration."""

_LIST_ELEMENT_DELIMITER = "#"
"""Delimiter separating the list elements within a serialized configuration (fade in steps and color groups)."""

_FIELD_DELIMITER = "|"
"""Delimiter separating the fields of a serialized list element (step fields and color group fields)."""

_ACCENT_COLOR_DELIMITER = "@"
"""Delimiter separating the serialized accent colors of a fade in step."""

_ASSET_DELIMITER = "?"
"""Delimiter separating the asset uuid from the fade in steps of a serialized color preset."""

_RECALL_DELIMITER = ";"
"""Delimiter separating the serialized recalls within the recalls configuration."""

_RECALL_STATE_DELIMITER = ","
"""Delimiter separating the color group states of a serialized recall."""

STEP_DURATION_MS = 40
"""Duration of a single fade in time step in milliseconds. Fade in times are stored as multiples of this step."""

_MAX_RECALL_COUNT = 1024
"""Maximum number of recalls that may be saved using filter messages."""

_DEFAULT_BUTTON_COLOR = ColorHSI(128.0, 0.5, 1.0)
"""Color used to represent color preset steps without accent colors in button visualizations."""


class ColorPreset:
    """A color preset.

    Contains all color steps with their fade in time (steps), transfer function and accent colors.

    """

    def __init__(self) -> None:
        """Initialize an empty color preset without steps and visualization asset."""
        self.colors: list[tuple[int, TransferFunction, list[ColorHSI]]] = []
        self._asset: AbstractImageAsset | str | None = None

    @classmethod
    def from_filter_str(cls, filter_str: str) -> ColorPreset:
        """Initialize a color preset from its serialized filter configuration string.

        Args:
            filter_str: Filter string representation to deserialize. An empty string will initialize an empty
                preset. Malformed steps and steps containing malformed accent colors are ignored. Steps without
                accent colors keep an empty color list.

        Returns:
            The deserialized color preset.

        """
        preset = cls()
        if _ASSET_DELIMITER in filter_str:
            asset_uuid, filter_str = filter_str.split(_ASSET_DELIMITER, 1)
            preset._asset = asset_uuid
        if len(filter_str) > 0:
            for step_str in filter_str.split(_LIST_ELEMENT_DELIMITER):
                try:
                    duration_str, transfer_function_str, colors_str = step_str.split(_FIELD_DELIMITER)
                    duration = int(duration_str)
                    transfer_function = TransferFunction(transfer_function_str)
                    colors = [
                        ColorHSI.from_filter_str(part, strict=True)
                        for part in colors_str.split(_ACCENT_COLOR_DELIMITER)
                        if len(part) > 0
                    ]
                except ValueError:
                    continue
                preset.colors.append((duration, transfer_function, colors))
        return preset

    def get_button_visualization(self) -> list[ColorHSI]:
        """Get the representation sequence for highlighting purposes in buttons.

        Returns:
            The first accent color of each step. Steps without colors are represented by the default color.

        """
        return [t[2][0] if t[2] else _DEFAULT_BUTTON_COLOR for t in self.colors]

    def serialize(self) -> str:
        """Serialize the preset to a string."""
        parts: list[str] = []
        for duration, transfer_function, colors in self.colors:
            accent_colors = _ACCENT_COLOR_DELIMITER.join(c.format_for_filter() for c in colors)
            parts.append(_FIELD_DELIMITER.join((str(duration), transfer_function.value, accent_colors)))
        list_str = _LIST_ELEMENT_DELIMITER.join(parts)
        asset = self.visualization_asset
        if asset is not None:
            return f"{asset.id}{_ASSET_DELIMITER}{list_str}"
        if isinstance(self._asset, str):
            return f"{self._asset}{_ASSET_DELIMITER}{list_str}"
        return list_str

    @property
    def visualization_asset(self) -> AbstractImageAsset | None:
        """Optional image used to represent the preset."""
        if isinstance(self._asset, str):
            resolved_asset = get_asset_by_uuid(self._asset)
            if not isinstance(resolved_asset, AbstractImageAsset):
                return None
            self._asset = resolved_asset
        return self._asset if isinstance(self._asset, AbstractImageAsset) else None

    @visualization_asset.setter
    def visualization_asset(self, asset: AbstractImageAsset | None) -> None:
        self._asset = asset


def _sanitize_channel_name(name: str) -> str:
    """Remove characters that are problematic within channel names from the provided name.

    Args:
        name: The channel name to sanitize.

    Returns:
        The sanitized channel name.

    """
    return name.strip().replace(":", "").replace("#", "").replace("|", "").replace(" ", "_").replace("__", "-")


def is_valid_channel_name(name: str) -> bool:
    """Check whether the provided color group or sub output name may be used.

    Only ASCII letters, digits, single underscores and hyphens are allowed since the names are used within filter
    ids, network update messages and serialized show files.

    Args:
        name: The name to check.

    Returns:
        True if the name is valid and can be used as color group or sub output name.

    """
    if len(name) == 0 or "__" in name or name.endswith("_") or not name.isascii():
        return False
    return all(char.isalnum() or char in "_-" for char in name)


def bound_preset_index(preset_index: int, preset_count: int) -> int:
    """Bound the provided color preset index to the available color presets.

    Args:
        preset_index: The color preset index to bound.
        preset_count: The number of available color presets.

    Returns:
        The provided index if it addresses one of the available color presets. Zero if the provided index is invalid.

    """
    if 0 <= preset_index < preset_count:
        return preset_index
    return 0


class SignalProvider(QObject):
    """Class provides a QObject in order to enable filters using signals."""

    mapped_signal = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Initialize a SignalProvider."""
        super().__init__(parent)


class ColordirectorVFilter(VirtualFilter):
    """VFilter to provide selectable colors.

    A Color Director is a filter that provides color values to defined color groups.
    Color sequences and accent colors can be defined. Accent colors will be evenly distributed into the channels of
    each color group.

    Saved recalls can set color selections based on the stored settings.

    Internally cue filters are used for each color group and presets are cues within them.
    Accent colors are distributed using the formula `SubOut[i] = accent colors[i mod #accent colors]`.
    If the apply all buttons of the UI widget are pressed, the state will be applied to all cues.
    Fade-in times are stored as multiples of the step duration defined by STEP_DURATION_MS.

    Setting live_preview_mode to true causes the filter to instantiate color constants that can be used instead of cues.

    """

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int, int] | tuple[float, float] | None = None) -> None:
        """Initializes the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLORDIRECTOR, pos=pos)
        self._color_groups: dict[str, list[str]] = {}
        self._presets: list[ColorPreset] = []
        self._recalls: list[list[int]] = []
        self.in_data_types["time"] = DataType.DT_DOUBLE
        self.in_data_types["time_scale"] = DataType.DT_DOUBLE
        self._registered_callbacks: list[tuple[int, str]] = []
        self._current_active_colors: list[int] = []
        self._cue_filter_to_group_index_mapping: dict[str, int] = {}
        self.configuration_changed = SignalProvider()
        self.live_preview_mode: bool = False
        self.live_preview_prompted: bool = False

    @property
    def presets(self) -> list[ColorPreset]:
        """Get the color presets.

        Returns:
            A shallow copy of the color preset list. The preset objects themselves are owned by the filter:
            Changes applied to them are reflected within the filter. Structural changes of the list need to be
            performed using add_preset, remove_preset and populate_presets_with_initial_data since they emit the
            configuration_changed signal.

        """
        return list(self._presets)

    def add_preset(self, preset: ColorPreset) -> None:
        """Add the provided color preset to the end of the color preset list.

        Args:
            preset: The color preset to add.

        """
        self._presets.append(preset)
        self.configuration_changed.mapped_signal.emit()

    def remove_preset(self, preset: ColorPreset) -> bool:
        """Remove the provided color preset from the color preset list.

        Args:
            preset: The color preset to remove.

        Returns:
            True if the color preset was removed. False if it is not part of the filter.

        """
        try:
            self._presets.remove(preset)
        except ValueError:
            return False
        self.configuration_changed.mapped_signal.emit()
        return True

    @property
    def output_groups(self) -> dict[str, list[str]]:
        """Get the color output group dictionary.

        Returns:
            A shallow copy of the color group dictionary. The sub output lists of the individual groups are
            owned by the filter: Structural changes need to be performed using add_output_group,
            add_sub_output, remove_sub_output and remove_output_group.

        """
        return dict(self._color_groups)

    def remove_output_group(self, group_name: str) -> None:
        """Remove the provided color group including its entries within the saved recalls.

        The currently active color selections are adjusted as well so their indexes keep matching the remaining
        color groups.

        Args:
            group_name: The name of the color group to remove. Unknown group names are ignored.

        """
        if group_name not in self._color_groups:
            return
        group_index = list(self._color_groups.keys()).index(group_name)
        del self._color_groups[group_name]
        for recall in self._recalls:
            if group_index < len(recall):
                recall.pop(group_index)
        if group_index < len(self._current_active_colors):
            self._current_active_colors.pop(group_index)
        self.configuration_changed.mapped_signal.emit()

    def add_output_group(self, group_name: str) -> bool:
        """Add a new color group without sub outputs.

        Args:
            group_name: The name of the color group to add.

        Returns:
            True if the color group was added. False if the name is invalid or already in use.

        """
        if not is_valid_channel_name(group_name) or group_name in self._color_groups:
            return False
        self._color_groups[group_name] = []
        self.configuration_changed.mapped_signal.emit()
        return True

    def add_sub_output(self, group_name: str, sub_output: str) -> bool:
        """Add a sub output to the provided color group.

        Args:
            group_name: The name of the color group to extend.
            sub_output: The name of the sub output to add.

        Returns:
            True if the sub output was added. False if the color group is unknown, the sub output name is
            invalid or already in use within the group.

        """
        if group_name not in self._color_groups:
            return False
        if not is_valid_channel_name(sub_output) or sub_output in self._color_groups[group_name]:
            return False
        self._color_groups[group_name].append(sub_output)
        self.configuration_changed.mapped_signal.emit()
        return True

    def remove_sub_output(self, group_name: str, sub_output: str) -> bool:
        """Remove the sub output from the provided color group.

        Args:
            group_name: The name of the color group to shrink.
            sub_output: The name of the sub output to remove.

        Returns:
            True if the sub output was removed. False if the color group or the sub output is unknown.

        """
        if group_name not in self._color_groups:
            return False
        channels = self._color_groups[group_name]
        if sub_output not in channels:
            return False
        channels.remove(sub_output)
        self.configuration_changed.mapped_signal.emit()
        return True

    @property
    def recalls(self) -> list[list[int]]:
        """Get the saved recalls.

        Returns:
            A shallow copy of the list of recalls. The recall lists themselves are owned by the filter:
            Modifications need to be performed using add_recall, remove_recall and set_recall_preset since they
            emit the configuration_changed signal.

        """
        return list(self._recalls)

    def add_recall(self) -> list[int]:
        """Add a new recall selecting the first color preset for every color group.

        Returns:
            The newly created recall. The returned list is owned by the filter and shared with the list
            returned by the recalls property.

        """
        recall: list[int] = [0] * len(self._color_groups)
        self._recalls.append(recall)
        self.configuration_changed.mapped_signal.emit()
        return recall

    def remove_recall(self, recall_index: int) -> None:
        """Remove the recall with the provided index.

        Args:
            recall_index: The index of the recall to remove. Unknown recall indices are ignored.

        """
        if not 0 <= recall_index < len(self._recalls):
            return
        self._recalls.pop(recall_index)
        self.configuration_changed.mapped_signal.emit()

    def set_recall_preset(self, recall_index: int, group_index: int, preset_index: int) -> bool:
        """Set the color preset index stored by a recall for a single color group.

        Args:
            recall_index: The index of the recall to modify.
            group_index: The index of the color group to store the value for.
            preset_index: The color preset index to store.

        Returns:
            True if the value was stored. False if the recall index or the color group index is unknown.

        """
        if not 0 <= recall_index < len(self._recalls) or group_index < 0:
            return False
        self.normalize_recall(recall_index)
        recall = self._recalls[recall_index]
        if group_index >= len(recall):
            return False
        recall[group_index] = bound_preset_index(preset_index, len(self._presets))
        self.configuration_changed.mapped_signal.emit()
        return True

    def normalize_recall(self, recall_index: int) -> None:
        """Normalize the recall with the provided index to the current number of color groups.

        Missing entries are filled with zeros. Surplus entries are removed. Unknown recall indices are ignored.

        Args:
            recall_index: The index of the recall to normalize.

        """
        if not 0 <= recall_index < len(self._recalls):
            return
        recall = self._recalls[recall_index]
        group_count = len(self._color_groups)
        while len(recall) < group_count:
            recall.append(0)
        del recall[group_count:]

    def get_recall_preset_selection(self, recall_index: int) -> list[tuple[str, int]] | None:
        """Get the color preset selection stored by a recall.

        This is the only place resolving the content of a recall: Both the filter message handling and the show
        UI widgets use it to apply recalls.

        Args:
            recall_index: The index of the recall to resolve.

        Returns:
            A list containing the name of every color group and the color preset index to apply to it. Stored
            indices that do not address one of the available color presets are bounded to the first color
            preset. None if the recall index is unknown or no color presets are available.

        """
        if not 0 <= recall_index < len(self._recalls):
            return None
        if len(self._presets) == 0:
            return None
        recall = self._recalls[recall_index]
        selection: list[tuple[str, int]] = []
        for group_index, group_name in enumerate(self._color_groups.keys()):
            stored_index = recall[group_index] if group_index < len(recall) else 0
            preset_index = bound_preset_index(stored_index, len(self._presets))
            if preset_index != stored_index:
                logger.warning(
                    "Recall %i stores the invalid color preset index %i for group '%s'. Falling back to the "
                    "first color preset.",
                    recall_index,
                    stored_index,
                    group_name,
                )
            selection.append((group_name, preset_index))
        return selection

    def get_accent_color_count(self) -> int:
        """Get the maximum number of accent colors in presets."""
        maximum = 0
        for preset in self.presets:
            for _, _, colors in preset.colors:
                maximum = max(maximum, len(colors))
        return maximum

    def _deserialize_color_groups(self) -> None:
        self._color_groups.clear()
        self.out_data_types.clear()
        color_group_def = self.filter_configurations.get("colorgroups", "")
        if len(color_group_def) == 0:
            return
        for group_def in color_group_def.split(_LIST_ELEMENT_DELIMITER):
            if len(group_def) == 0:
                continue
            output_channels = group_def.split(_FIELD_DELIMITER)
            group_name = _sanitize_channel_name(output_channels[0])
            if group_name != output_channels[0]:
                logger.warning(
                    "Renaming the color group '%s' to '%s' while deserializing.", output_channels[0], group_name
                )
            if not is_valid_channel_name(group_name):
                logger.warning("Ignoring the color group '%s' because its name is invalid.", output_channels[0])
                continue
            if group_name in self._color_groups:
                logger.warning("Ignoring the color group '%s' because its name is already in use.", group_name)
                continue
            output_channels.pop(0)
            channels: list[str] = []
            for channel in output_channels:
                channel_name = _sanitize_channel_name(channel)
                if channel_name != channel:
                    logger.warning(
                        "Renaming the sub output '%s' of the color group '%s' to '%s' while deserializing.",
                        channel,
                        group_name,
                        channel_name,
                    )
                if not is_valid_channel_name(channel_name):
                    logger.warning(
                        "Ignoring the sub output '%s' of the color group '%s' because its name is invalid.",
                        channel,
                        group_name,
                    )
                    continue
                if channel_name in channels:
                    logger.warning(
                        "Ignoring the sub output '%s' because its name is already in use within the color group '%s'.",
                        channel_name,
                        group_name,
                    )
                    continue
                channels.append(channel_name)
            self._color_groups[group_name] = channels
            for chan_name in channels:
                self.out_data_types[f"{group_name}__{chan_name}"] = DataType.DT_COLOR

    def _serialize_color_groups(self) -> None:
        self.filter_configurations["colorgroups"] = _LIST_ELEMENT_DELIMITER.join(
            _FIELD_DELIMITER.join([_sanitize_channel_name(name), *(_sanitize_channel_name(c) for c in channels)])
            for name, channels in self._color_groups.items()
        )

    def _deserialize_presets(self) -> None:
        self._presets.clear()
        presets_def = self.filter_configurations.get("presets", "")
        if len(presets_def) == 0:
            return
        self._presets.extend(ColorPreset.from_filter_str(p_str) for p_str in presets_def.split(_PRESET_DELIMITER))

    def _serialize_presets(self) -> None:
        self.filter_configurations["presets"] = _PRESET_DELIMITER.join(c.serialize() for c in self._presets)

    def _serialize_recalls(self) -> None:
        self.filter_configurations["recalls"] = _RECALL_DELIMITER.join(
            _RECALL_STATE_DELIMITER.join(str(state) for state in states) for states in self._recalls
        )

    def _deserialize_recalls(self) -> None:
        self._recalls.clear()
        recalls_def = self.filter_configurations.get("recalls", "")
        if len(recalls_def) == 0:
            return
        for recall_def in recalls_def.split(_RECALL_DELIMITER):
            if len(recall_def) == 0:
                continue
            recall: list[int] = []
            for state in recall_def.split(_RECALL_STATE_DELIMITER):
                if len(state) == 0:
                    continue
                try:
                    recall.append(int(state))
                except ValueError:
                    recall.append(0)
            self._recalls.append(recall)

    def populate_presets_with_initial_data(self, short: bool) -> None:
        """Populate the color presets with common initial data.

        This method will generate color presets for the most common color choices and replace all existing presets.
        The default fade-in is linear with a fade-in time of three seconds.

        Args:
            short: If set to true, a smaller preset field will be generated.

        """
        self._presets.clear()

        steps_per_second: int = 1000 // STEP_DURATION_MS
        three_second_fade: int = steps_per_second * 3

        white = ColorPreset()
        white.colors.append((three_second_fade, TransferFunction.LINEAR, [ColorHSI(0.0, 0.0, 1.0)]))
        self._presets.append(white)

        if short:
            pink = ColorPreset()
            pink.colors.append((three_second_fade, TransferFunction.LINEAR, [ColorHSI(296.0, 0.89, 1.0)]))
            self._presets.append(pink)
            for hue in (0.0, 25.0, 60.0, 114.0, 170.0, 227.0, 265.0):
                color = ColorPreset()
                color.colors.append((three_second_fade, TransferFunction.LINEAR, [ColorHSI(hue, 1.0, 1.0)]))
                self._presets.append(color)
        else:
            for hue in range(0, 360, 18):
                color = ColorPreset()
                color.colors.append((three_second_fade, TransferFunction.LINEAR, [ColorHSI(hue, 1.0, 1.0)]))
                self._presets.append(color)
        self.configuration_changed.mapped_signal.emit()

    def get_outputs(self) -> list[str]:
        """Get the outputs of this filter."""
        output_list: list[str] = []
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
        parts = virtual_port_id.split("__")
        if len(parts) != 2:
            return None
        color_group_name, group_output_channel = parts
        if color_group_name not in self._color_groups:
            return None
        color_group = self._color_groups[color_group_name]
        if group_output_channel not in color_group:
            return None
        if self.live_preview_mode:
            return f"{self.filter_id}__preview_const__{color_group_name}__{group_output_channel}:value"
        return f"{self.filter_id}__cue__{color_group_name}:{group_output_channel}"

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        if self.live_preview_mode:
            self._inst_filters_preview_mode(filter_list)
        else:
            self._inst_filters_normal_mode(filter_list)

    def _clear_runtime_state(self) -> None:
        """Remove all runtime state that was populated by a previous filter instantiation.

        This unregisters all filter update callbacks and forgets the currently active color presets. It needs to
        be called before the filters are instantiated anew, independent of the instantiation mode.
        """
        for scene_id, filter_id in self._registered_callbacks:
            self.scene.board_configuration.clear_filter_update_callbacks(scene_id, filter_id)
        self._registered_callbacks.clear()
        self._current_active_colors.clear()
        self._cue_filter_to_group_index_mapping.clear()

    def _inst_filters_normal_mode(self, filter_list: list[Filter]) -> None:
        self._clear_runtime_state()
        timescale_input = self.channel_links.get("time_scale")
        if timescale_input is None:
            float_const = Filter(
                self.scene,
                f"{self.filter_id}__timescale_const",
                FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                pos=self.pos,
                initial_parameters={"value": "1.0"},
            )
            timescale_input = float_const.filter_id + ":value"
            filter_list.append(float_const)
        time_input = self.channel_links.get("time")
        if time_input is None:
            time_filter = Filter(
                self.scene, f"{self.filter_id}__time", FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT, pos=self.pos
            )
            time_input = time_filter.filter_id + ":value"
            filter_list.append(time_filter)
        for group_index, item in enumerate(self._color_groups.items()):
            color_group_name, output_channels = item
            cue_filter = CueFilter(
                self.scene, f"{self.filter_id}__cue__{_sanitize_channel_name(color_group_name)}", pos=self.pos
            )
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
                    last_time += fadein_time * STEP_DURATION_MS
                    kf.timestamp = last_time / 1000.0
                    if len(colors) > 0:
                        for i in range(len(output_channels)):
                            state = StateColor(transfer_function.value)
                            state.color = colors[i % len(colors)]
                            kf.append_state(state)
                    # steps without accent colors generate a stateless key frame that holds all channel values
                    # until the next step begins
                    cue.insert_frame(kf)
                cue.end_action = EndAction.HOLD if len(preset.colors) < 2 else EndAction.START_AGAIN
            if len(self._presets) > 0:
                cfm.default_cue = 0
            cue_filter.filter_configurations.update(cfm.get_as_configuration())
            cue_filter.instantiate_filters(filter_list)
            self.scene.board_configuration.register_filter_update_callback(
                self.scene.scene_id, cue_filter.filter_id, self._update_active_colors_from_filters
            )
            self._registered_callbacks.append((self.scene.scene_id, cue_filter.filter_id))
            self._cue_filter_to_group_index_mapping[cue_filter.filter_id] = group_index

    def _inst_filters_preview_mode(self, filter_list: list[Filter]) -> None:
        self._clear_runtime_state()
        for output_group, sub_outputs in self._color_groups.items():
            for sub_output in sub_outputs:
                color_const_filter = Filter(
                    self.scene,
                    f"{self.filter_id}__preview_const__{output_group}__{sub_output}",
                    FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
                    self.pos,
                    {},
                    {"value": "0.0,0.0,1.0"},
                )
                filter_list.append(color_const_filter)

    def apply_colors_on_preview_constants(self, accent_colors: list[ColorHSI]) -> None:
        """Apply the provided colors to the preview constants.

        This method needs to be called from a Qt Event Thread. It will fail if the filter is not in live preview mode
        or the scene has not been applied.

        """
        if not self.live_preview_mode:
            return
        if len(accent_colors) == 0:
            accent_colors = [ColorHSI(0.0, 0.0, 1.0)]
        nm = NetworkManager()
        for output_group, sub_outputs in self._color_groups.items():
            for i, sub_output in enumerate(sub_outputs):
                nm.send_gui_update_to_fish(
                    self.scene.scene_id,
                    f"{self.filter_id}__preview_const__{output_group}__{sub_output}",
                    "value",
                    accent_colors[i % len(accent_colors)].format_for_filter(),
                    enque=True,
                )
        self._flush_pending_update_messages()

    @override
    def handle_filter_message(self, key: str, value: str) -> bool:
        """Handle filter messages sent by show UI widgets.

        The "save-selection-to-recall" message modifies the recalls stored within this filter. This modification is
        not tracked as an unsaved change of the show file yet: The show needs to be saved manually in order to keep
        recalls saved using filter messages.

        Args:
            key: The message key. Supported keys are "save-selection-to-recall", "recall", "call" and
                "call-column".
            value: The message value.

        Returns:
            True if the message was understood and handled. False otherwise.

        """
        match key:
            case "save-selection-to-recall":
                try:
                    target_recall = int(value)
                except ValueError:
                    return False
                if not 0 <= target_recall < _MAX_RECALL_COUNT:
                    return False
                current_colors = self.get_current_active_colors()
                if len(current_colors) == 0:
                    return False
                while len(self._recalls) <= target_recall:
                    self._recalls.append([0] * len(self._color_groups))
                selected_recall = self._recalls[target_recall]
                selected_recall.clear()
                selected_recall.extend(current_colors)
                logger.info("Saved the current color selection as recall %i.", target_recall)
                # TODO: mark the show as modified as soon as the editor tracks unsaved changes.
                self.configuration_changed.mapped_signal.emit()
                return True
            case "recall":
                try:
                    target_recall = int(value)
                except ValueError:
                    return False
                selection = self.get_recall_preset_selection(target_recall)
                if selection is None:
                    return False
                for group_name, preset_index in selection:
                    self._send_preset_change_update(group_name, preset_index)
                self._flush_pending_update_messages()
                return True
            case "call":
                try:
                    group_name, preset_index_str = value.split(",")
                    color_preset_index = int(preset_index_str)
                except ValueError:
                    return False
                if group_name not in self._color_groups:
                    return False
                if not 0 <= color_preset_index < len(self._presets):
                    return False
                self._send_preset_change_update(group_name, color_preset_index)
                self._flush_pending_update_messages()
                return True
            case "call-column":
                try:
                    preset_index = int(value)
                except ValueError:
                    return False
                if not 0 <= preset_index < len(self._presets):
                    return False
                for group_name in self._color_groups:
                    self._send_preset_change_update(group_name, preset_index)
                self._flush_pending_update_messages()
                return True
            case _:
                return False

    def _update_active_colors_from_filters(self, param: proto.FilterMode_pb2.update_parameter) -> None:
        """Update the currently active color presets from a cue filter update message.

        The cue filters generated by this virtual filter report started cues using update parameter values of the
        form "run;<color preset index>". This message format is defined by the cue filter implementation running on
        fish: Whenever it changes, this parsing needs to be adapted since format mismatches silently disable the
        active color feedback.

        Messages of unknown cue filters, malformed messages and invalid color preset indices are ignored, since they
        are received from the network.

        """
        group_index = self._cue_filter_to_group_index_mapping.get(param.filter_id)
        if group_index is None or not 0 <= group_index < len(self._color_groups):
            return
        parts = param.parameter_value.split(";")
        if len(parts) < 2:
            logger.debug(
                "Ignoring malformed cue filter update message of '%s': '%s'",
                param.filter_id,
                param.parameter_value,
            )
            return
        try:
            value = int(parts[1])
        except ValueError:
            logger.debug(
                "Ignoring cue filter update message of '%s' without an integer color preset index: '%s'",
                param.filter_id,
                param.parameter_value,
            )
            return
        if not 0 <= value < len(self._presets):
            logger.debug(
                "Ignoring cue filter update message of '%s' addressing the unknown color preset index %i.",
                param.filter_id,
                value,
            )
            return
        changed: bool = False
        if len(self._current_active_colors) == 0:
            self._current_active_colors.extend([0] * len(self._color_groups))
            changed = True
        if self._current_active_colors[group_index] != value:
            self._current_active_colors[group_index] = value
            changed = True
        if changed:
            self.configuration_changed.mapped_signal.emit()

    def get_current_active_colors(self) -> list[int]:
        """Get the current active color presets.

        Returns:
            A copy of the list of indexes or an empty list if the filter was not applied and did not receive
            updates. The internal list is updated asynchronously by network callbacks: Callers may iterate the
            returned list without having to expect concurrent modifications.

        """
        return list(self._current_active_colors)

    def _get_cue_update_msg(self, color_group_name: str, preset_index: int) -> tuple[str, str, str]:
        """Generate the network update message parts for applying a preset to a color group.

        Args:
            color_group_name: The key of the group to update.
            preset_index: The index of the preset to use.

        Returns:
            A tuple containing the target filter id, the update key and the update value.

        """
        return (
            f"{self.filter_id}__cue__{_sanitize_channel_name(color_group_name)}",
            "run_cue",
            str(preset_index),
        )

    def get_update_msg_for_group_preset_change(self, color_group_name: str, preset_index: int) -> tuple[str, str]:
        """Generate message to set the color group value to the given preset.

        Args:
            color_group_name: The key of the group to update.
            preset_index: The index of the preset to use.

        Returns:
            A tuple containing the [target filter ID]:[update key] and update value.

        """
        filter_id, msg_key, update_value = self._get_cue_update_msg(color_group_name, preset_index)
        return f"{filter_id}:{msg_key}", update_value

    def _send_preset_change_update(self, group_name: str, preset_index: int) -> None:
        """Enqueue a network update message that applies the provided preset to the provided color group.

        The message is only enqueued instead of being transmitted directly: Callers need to flush the pending update
        messages using _flush_pending_update_messages once all desired messages have been enqueued.
        """
        filter_id, msg_key, update_value = self._get_cue_update_msg(group_name, preset_index)
        NetworkManager().send_gui_update_to_fish(self.scene.scene_id, filter_id, msg_key, update_value, enque=True)

    def _flush_pending_update_messages(self) -> None:
        """Flush update messages enqueued by this filter to fish.

        Enqueued update messages are only transmitted once the message queue is flushed. Instead of relying on other
        components flushing the queue (such as the periodic fish state updates), this is done explicitly here. The
        flush is skipped while the connection to fish is not established, since no messages are enqueued in that
        case and the queue may still contain messages of other components waiting for a connection.

        This method needs to be called from the Qt event thread.
        """
        nm = NetworkManager()
        if nm.is_running:
            nm.push_messages()
