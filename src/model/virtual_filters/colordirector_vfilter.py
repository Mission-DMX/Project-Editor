"""Color Director vFilter."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from model.color_hsi import ColorHSI
from model.filter import FilterTypeEnumeration, VirtualFilter
from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
    from model import Filter
    from model.scene import Scene


class _ColorPreset:
    def __init__(self, filter_str: str = "") -> None:
        self.colors: list[tuple[int, TransferFunction, list[ColorHSI]]] = []
        if len(filter_str) > 0:
            for step_str in filter_str.split("#"):
                duration, transf, colors = step_str.split("|")
                duration = int(duration)
                transf = TransferFunction(transf)
                colors = [ColorHSI.from_filter_str(part) for part in colors.split("@")]
                self.colors.append((duration, transf, colors))

    def get_button_visualization(self) -> list[ColorHSI]:
        return [t[2][0] for t in self.colors]

    def serialize(self) -> str:
        parts: list[str] = []
        for duration, transfer_function, colors in self.colors:
            parts.append(f"{duration}|{transfer_function.value}|{"@".join(c.format_for_filter() for c in colors)}")
        return "#".join(parts)


def _sanitize_channel_name(name: str) -> str:
    return name.replace(":", "").replace("#", "").replace("|", "").strip()


class ColordirectorVFilter(VirtualFilter):
    """VFilter to provide selectable colors.

    A Color Director is a filter that provides color values to defined color groups.
    Color sequences and accent colors can be defined. Accent colors will be evenly distributed into the channels of
    each color group.

    Internally cue filters are used for each color group and presets are cues within them.
    Accent colors are distributed using the formula `SubOut[i] = accent colors[i mod #accent colors]`.
    If the apply all buttons of the UI widget are pressed, the state will be applied to all cues.
    Fade-in curves are stored with the new steps per second time reference.

    """

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Initializes the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLORDIRECTOR, pos=pos)
        self._color_groups: dict[str, list[str]] = {}
        self._presets: list[_ColorPreset] = []
        # TODO setup time and timescale input channels

    def _deserialize_color_groups(self) -> None:
        self._color_groups.clear()
        color_group_def = self.filter_configurations.get("colorgroups", "")
        if len(color_group_def) == 0:
            return
        for group_def in color_group_def.split("#"):
            output_channel = group_def.split("|")
            if len(output_channel) < 1:
                raise ValueError("A least a name of the color group must be defined.")
            name = output_channel[0]
            output_channel.pop(0)
            self._color_groups[name] = output_channel

    def _serialize_color_groups(self) -> None:
        self.filter_configurations["colorgroups"] = "#".join(f"{_sanitize_channel_name(name)}|{
            "|".join(_sanitize_channel_name(c) for c in channels)}" for name, channels in self._color_groups.items())

    def _deserialize_presets(self) -> None:
        self._presets.clear()
        presets_def = self.filter_configurations.get("presets", "")
        if len(presets_def) == 0:
            return
        self._presets.extend(_ColorPreset(p_str) for p_str in presets_def.split("$"))

    def _serialize_presets(self) -> None:
        self._filter_configurations["presets"] = "$".join(c.serialize() for c in self._presets)

    def populate_presets_with_initial_data(self, short: bool) -> None:
        """Populate the color presets with common initial data.

        This method will generate color presets for the most common color choices.
        The default fade-in is linear with a fade-in time of three seconds.

        Args:
            short: If set to true, a smaller preset field will be generated.

        """
        steps_per_second: int = int(1000 / 40)
        three_secs: int = steps_per_second * 3

        white = _ColorPreset()
        white.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(0, 0, 1)]))
        self._presets.append(white)

        if short:
            pink = _ColorPreset()
            pink.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(296.0, 0.89, 1)]))
            self._presets.append(pink)
            red = _ColorPreset()
            red.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(360.0, 1, 1)]))
            self._presets.append(red)
            orange = _ColorPreset()
            orange.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(25, 1, 1)]))
            self._presets.append(orange)
            yellow = _ColorPreset()
            yellow.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(60.0, 1, 1)]))
            self._presets.append(yellow)
            green = _ColorPreset()
            green.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(114.0, 1, 1)]))
            self._presets.append(green)
            cyan = _ColorPreset()
            cyan.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(170.0, 1, 1)]))
            self._presets.append(cyan)
            blue = _ColorPreset()
            blue.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(227, 1, 1)]))
            self._presets.append(blue)
            purple = _ColorPreset()
            purple.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(265.0, 1, 1)]))
            self._presets.append(purple)
        else:
            for hue in range(0, 360, 18):
                color = _ColorPreset()
                color.colors.append((three_secs, TransferFunction.LINEAR, [ColorHSI(hue, 1, 1)]))
                self._presets.append(color)

    def _update_outputs(self) -> None:
        pass  # TODO

    @override
    def serialize(self) -> None:
        super().serialize()
        self._serialize_color_groups()
        self._serialize_presets()

    @override
    def deserialize(self) -> None:
        super().deserialize()
        self._deserialize_color_groups()
        self._deserialize_presets()
        self._update_outputs()

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        pass  # TODO

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        pass  # TODO

    @override
    def handle_filter_message(self, key: str, value: str) -> bool:
        pass  # TODO
