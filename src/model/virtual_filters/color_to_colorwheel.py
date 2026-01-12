"""Contains ColorToColorwheel vFilter."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, override

from jinja2 import Environment

from model.filter import Filter, FilterTypeEnumeration, VirtualFilter
from utility import resource_path

if TYPE_CHECKING:
    from jinja2.environment import Template

    from model import Scene

with open(resource_path(os.path.join("resources", "data", "color-to-colorwheel-template.lua.j2")), "r") as f:
    _FILTER_CONTENT_TEMPLATE: Template = Environment().from_string(f.read())  # NOQA: S701 the editor is not a web page.


class ColorToColorWheel(VirtualFilter):
    """A vFilter that takes a color channel as an input and maps it to a color wheel channel."""

    def __init__(self, scene: Scene, filter_id: str, pos: tuple[int] | None = None) -> None:
        """Initialize the vFilter.

        The following filter configuration properties are available:
         - mode: Either automatic (the filter loads its color points from the fixture) or manual.
         - fixture-uuid: The fixture UUID to use in automatic mode.
         - color-mappings: The color mappings to use in manual mode. Format: h:s:cw;h:s:cw;...
         - dimmer-input: Should a dimmer input be used? Can either be "8bit", "16bit", "float" or "".
         - dimmer-output: The data type of the dimmer output channel. Can either be "8bit", "16bit", "float" or "".
         - colorwheel-datatype: The data type of the color wheel slot. Can either be "8bit" or "16bit".
         - wheel_speed: Time in ms to switch between two adjacent wheel slots in manual mode.
         - dim_when_off: If true, the brightness will be suspended as long as the wrong color wheel slot is dialed in.

        The following ports are provided:
         - input: The color input channel (input, color)
         - in_dimmer: Optional, Input dimmer mixin (input, 8bit or 16bit or float)
         - dimmer: Output dimmer channel (output, 8bit or 16bit or float)
         - colorwheel: The color wheel slot to use (output, 8bit or 16bit)

        Args:
            scene: The scene to use for this filter.
            filter_id: The id of the filter to use.
            pos: Optional, The position of the filter to use.

        """
        super().__init__(scene, filter_id, FilterTypeEnumeration.VFILTER_COLOR_TO_COLORWHEEL, pos=pos)
        if "mode" not in self._filter_configurations:
            self.filter_configurations["mode"] = "automatic"
        if "fixture-uuid" not in self._filter_configurations:
            self.filter_configurations["fixture-uuid"] = ""
        if "color-mappings" not in self._filter_configurations:
            self.filter_configurations["color-mappings"] = ""
        if "dimmer-input" not in self._filter_configurations:
            self.filter_configurations["dimmer-input"] = "8bit"
        if "dimmer-output" not in self._filter_configurations:
            self.filter_configurations["dimmer-output"] = ""
        if "colorwheel-datatype" not in self._filter_configurations:
            self.filter_configurations["colorwheel-datatype"] = "8bit"
        if "wheel_speed" not in self.filter_configurations:
            self.filter_configurations["wheel_speed"] = "300"
        if "dim_when_off" not in self.filter_configurations:
            self.filter_configurations["dim_when_off"] = "true"

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        if virtual_port_id not in ["dimmer", "colorwheel"]:
            raise ValueError(f"Invalid virtual port ID. Filter ID: {self.filter_id}, Requested Port: {virtual_port_id}")
        return f"{self.filter_id}:{virtual_port_id}"

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        if self.filter_configurations["mode"] == "automatic":
            # TODO
            raise ValueError(f"Automatic mode is currently not implemented. Filter ID: {self.filter_id}")
        input_dimmer_channel = self.channel_links.get("in_dimmer", "")
        hue_values: list[float] = []
        saturation_values: list[float] = []
        slots: list[int] = []
        required_dimmer_output_data_type = self.filter_configurations["dimmer-output"]
        dimmer_input_data_type = self.filter_configurations["dimmer-input"]

        colorwheel_is_16bit = self.filter_configurations["colorwheel-datatype"] == "16bit"

        input_dimmer_configured = input_dimmer_channel != ""
        dimmer_output_required = required_dimmer_output_data_type != ""
        wheel_speed = self.filter_configurations.get("wheel_speed", "300")

        for mapping_str in self.filter_configurations.get("color-mappings", "").split(";"):
            hue, saturation, slot = mapping_str.split(":")
            hue_values.append(float(hue))
            saturation_values.append(float(saturation))
            slots.append(int(slot))

        match required_dimmer_output_data_type:
            case "8bit":
                output_dimmer_multiplier = "255"
            case "16bit":
                output_dimmer_multiplier = "65535"
            case _:
                output_dimmer_multiplier = "1"

        match dimmer_input_data_type:
            case "8bit":
                input_dimmer_multiplier = "255"
            case "16bit":
                input_dimmer_multiplier = "65535"
            case _:
                input_dimmer_multiplier = "1"

        script = _FILTER_CONTENT_TEMPLATE.render({
            "input_dimmer_channel_connected": input_dimmer_configured,
            "input_dimmer_channel_data_type": dimmer_input_data_type,
            "input_dimmer_multiplier": input_dimmer_multiplier,
            "hue_values": hue_values,
            "saturation_values": saturation_values,
            "slots": slots,
            "wheel_speed": wheel_speed,
            "dimmer_output_required": dimmer_output_required,
            "output_dimmer_data_type": required_dimmer_output_data_type,
            "output_dimmer_multiplier": output_dimmer_multiplier,
            "dim_when_off": self.filter_configurations.get("dim_when_off", "true") == "true",
            "colorwheel_datatype": self.filter_configurations.get("colorwheel-datatype", "8bit"),
        })

        f = Filter(self.scene, self.filter_id, FilterTypeEnumeration.FILTER_SCRIPTING_LUA, pos=self.pos)
        f.initial_parameters["script"] = script
        f.filter_configurations["in_mapping"] = "input:color;time:float"
        if input_dimmer_configured:
            f.filter_configurations["in_mapping"] += f";in_dimmer:{dimmer_input_data_type}"
        f.filter_configurations["out_mapping"] = f"colorwheel:{"16bit" if colorwheel_is_16bit else "8bit"}"
        if dimmer_output_required:
            f.filter_configurations["out_mapping"] += f";dimmer:{required_dimmer_output_data_type}"
        f.channel_links.update(self.channel_links)
        filter_list.append(f)
