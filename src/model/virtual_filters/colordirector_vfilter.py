from __future__ import annotations

from typing import TYPE_CHECKING

from model import Filter
from model.color_hsi import ColorHSI
from model.filter import VirtualFilter, FilterTypeEnumeration
from model.filter_data.transfer_function import TransferFunction

if TYPE_CHECKING:
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


class ColordirectorVFilter(VirtualFilter):
    """VFilter to provide selectable colors."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Initializes the virtual filter."""
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLORDIRECTOR, pos=pos)
        self._color_groups: dict[str, list[str]] = {}
        self._presets: list[_ColorPreset] = []
        # TODO load color groups
        # TODO load presets

    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        pass  # TODO

    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        pass  # TODO

    # TODO write serialization function