# coding=utf-8

"""This file contains the effects of type color."""

from abc import ABC, abstractmethod
from typing import Any

from PySide6.QtWidgets import QWidget

from model import Filter
from model.filter import FilterTypeEnumeration
from model.virtual_filters.effects_stacks.adapters import emplace_with_adapter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from view.show_mode.effect_stacks.configuration_widgets.color_wheel_configuration_widget import \
    ColorWheelConfigurationWidget


class ColorEffect(Effect, ABC):
    def get_output_slot_type(self):
        return EffectType.COLOR


class ColorWheelEffect(ColorEffect):
    """This effect provides a color wheel. Besides implementing the base methods, it provides further methods to set
    the default hue range and number of segments."""

    EFFECT_ID = "effect.colors.colorwheel"

    def __init__(self):
        super().__init__({"speed": [EffectType.SPEED],
                          "range": [EffectType.GENERIC_NUMBER],
                          "segments": [EffectType.LIGHT_INTENSITY, EffectType.ENABLED_SEGMENTS]})
        self._number_of_fragments: int = 0
        self._min_hue: float = 0.0
        self._max_hue: float = 360.0
        self._default_speed: float = 30.0
        self._widget = ColorWheelConfigurationWidget(self)

    def get_serializable_effect_name(self) -> str:
        return self.EFFECT_ID

    def get_configuration_widget(self) -> QWidget | None:
        return self._widget

    def resolve_input_port_name(self, slot_id: str) -> str:
        match slot_id:
            case "speed":
                return "Speed"
            case "range":
                return "Color Range"
            case "segments":
                return "Segment Brightness"
        return "Not Implemented"

    def emplace_filter(self, filter_list: list[Filter], prefix: str) -> dict[str, str | list[str]]:
        fragment_outputs = []
        speed_effect = self._inputs["speed"]
        if speed_effect:
            speed_input_channel = emplace_with_adapter(speed_effect, EffectType.GENERIC_NUMBER,
                                                       filter_list, prefix + "__speed_")["x"]
        else:
            speed_effect_name = prefix + "_speedconst"
            speed_effect = Filter(self.get_scene(), speed_effect_name, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                                  self.get_position())
            speed_effect.initial_parameters["value"] = str(self._default_speed)  # TODO normalize to 1/60
            filter_list.append(speed_effect)
            speed_input_channel = speed_effect_name + ":value"
        # TODO inst range input filter or place constants using min and max hue
        range_input = self._inputs["range"]
        if range_input is not None:
            hue_effect_range_factor_channel = emplace_with_adapter(range_input,
                                                                   EffectType.GENERIC_NUMBER,
                                                                   filter_list, prefix + "__range_")["x"]
        else:
            hue_effect_range_factor_name = prefix + "__range_const_min"
            filter_list.append(Filter(self.get_scene(), hue_effect_range_factor_name,
                               FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, self.get_position(),
                               initial_parameters={"value": "360.0"}))
            hue_effect_range_factor_channel = hue_effect_range_factor_name + ":value"

        saturation_input_filter_name = prefix + "__saturation"
        filter_list.append(Filter(self.get_scene(), saturation_input_filter_name, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                                  initial_parameters={"value": "1.0"}))

        # TODO implement filter that iterates between the hue boundries using the speed as a fraction for the time input
        hue_effect_range_offset = prefix + "__hue_offset_const"
        filter_list.append(Filter(self.get_scene(), hue_effect_range_offset,
                                  FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, pos=self.get_position(),
                                  initial_parameters={"value": "180.0"}))

        time_filter_name = prefix + "__time"
        filter_list.append(Filter(self.get_scene(), time_filter_name, FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT))

        if self._inputs["segments"] is None:
            brightness_channel_name = prefix + "__brightness_const"
            filter_list.append(Filter(self.get_scene(), brightness_channel_name, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                                      initial_parameters={"value": "1.0"}))
            brightness_channel_name += ":value"
        else:
            brightness_channel_name = emplace_with_adapter(
                self._inputs["segments"],
                EffectType.LIGHT_INTENSITY
                if self._inputs["segments"].get_output_slot_type() != EffectType.ENABLED_SEGMENTS
                else EffectType.ENABLED_SEGMENTS,
                filter_list,
                prefix + "__segments_brightness_"
            )

        for frag_index in range(self.fragment_number):
            time_fraction_filter_name = prefix + "__time_fraction"
            time_fraction_filter = Filter(self.get_scene(), time_fraction_filter_name,
                                          FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN, self.get_position())
            phase_filter_name = prefix + "__phase"
            # TODO add option to place phase input effect
            filter_list.append(Filter(self.get_scene(), phase_filter_name, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                                      self.get_position(), {"value": "0"}))
            phase_filter_name += ":value"
            time_fraction_filter.channel_links["factor_inner"] = speed_input_channel
            time_fraction_filter.channel_links["factor_outer"] = hue_effect_range_factor_channel
            time_fraction_filter.channel_links["offset"] = hue_effect_range_offset + ":value"
            time_fraction_filter.channel_links["phase"] = phase_filter_name + ":value"
            time_fraction_filter.channel_links["value_in"] = time_filter_name + ":value"
            filter_list.append(time_fraction_filter)

            if "intensity" in brightness_channel_name.keys():
                brightness_channel_instance = brightness_channel_name["intensity"]
            else:
                brightness_channel_instance = brightness_channel_name[str(frag_index % len(brightness_channel_name))]

            color_conv_filter_name = prefix + "__color_conv"
            color_conv_filter = Filter(self.get_scene(), color_conv_filter_name, FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_COLOR)
            filter_list.append(color_conv_filter)
            color_conv_filter.channel_links["h"] = time_fraction_filter_name + ":value"
            color_conv_filter.channel_links["s"] = saturation_input_filter_name + ":value"
            color_conv_filter.channel_links["i"] = brightness_channel_instance
            fragment_outputs.append(color_conv_filter_name + ":value")

        return {"color": fragment_outputs}

    def get_human_filter_name(self):
        return "Color Wheel"

    def get_description(self):
        return "This effect cycles through a color wheel"

    @property
    def fragment_number(self) -> int:
        return self._number_of_fragments

    @fragment_number.setter
    def fragment_number(self, new_fragment_count: int):
        self._number_of_fragments = max(new_fragment_count, 1)

    @property
    def min_hue(self) -> float:
        return self._min_hue

    @min_hue.setter
    def min_hue(self, new_value: float):
        self._min_hue = new_value % 360.0

    @property
    def max_hue(self) -> float:
        return self._max_hue

    @max_hue.setter
    def max_hue(self, new_value: float):
        self._max_hue = new_value % 360.0

    def serialize(self) -> dict:
        d = {"type": self.EFFECT_ID,
             "number-of-fragments": self._number_of_fragments,
             "min-hue": self._min_hue,
             "max-hue": self._max_hue,
             "default-speed": self._default_speed}
        speed_input = self._inputs["speed"]
        if speed_input is not None:
            d["speed-input"] = speed_input.serialize()
        range_input = self._inputs["range"]
        if range_input is not None:
            d["range-input"] = range_input.serialize()
        return d

    def deserialize(self, data: dict[str, Any]):
        from model.virtual_filters.effects_stacks.effect_factory import effect_from_deserialization
        self._number_of_fragments = data['number-of-fragments']
        self._min_hue = data["min-hue"]
        self._max_hue = data["max-hue"]
        self._default_speed = data["default-speed"]
        speed_input_data = data.get("speed-input")
        if speed_input_data is not None:
            self._inputs["speed"] = effect_from_deserialization(speed_input_data, self._parent_filter)
        range_input_data = data.get("range-input")
        if range_input_data is not None:
            self._inputs["range"] = effect_from_deserialization(range_input_data, self._parent_filter)
        self._widget.load_values_from_effect()
