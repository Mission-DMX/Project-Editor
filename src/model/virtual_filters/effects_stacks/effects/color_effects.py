from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget

from model import Filter
from model.filter import FilterTypeEnumeration
from model.virtual_filters.effects_stacks.adapters import emplace_adapter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from view.show_mode.effect_stacks.configuration_widgets.color_wheel_configuration_widget import \
    ColorWheelConfigurationWidget


class ColorEffect(Effect, ABC):
    def get_output_slot_type(self):
        return EffectType.COLOR


class ColorWheelEffect(ColorEffect):

    EFFECT_ID = "effect.colors.colorwheel"

    def __init__(self):
        super().__init__({"speed": [EffectType.SPEED],
                          "range": [EffectType.GENERIC_NUMBER]})
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
        return "Not Implemented"

    def emplace_filter(self, filter_list: list[Filter], prefix: str) -> dict[str, str | list[str]]:
        speed_effect = self._inputs["speed"]
        if speed_effect:
            speed_input_channel = speed_effect.emplace_filter(filter_list, prefix + "__speed_")
            speed_input_channel = emplace_adapter(speed_effect.get_output_slot_type(), EffectType.GENERIC_NUMBER,
                                                  speed_input_channel, filter_list)["x"]
        else:
            speed_effect_name = prefix + "_speedconst"
            speed_effect = Filter(self.get_scene(), speed_effect_name, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                                  self.get_position())
            speed_effect.initial_parameters["value"] = str(self._default_speed)
            speed_input_channel = speed_effect_name + ":value"
        # TODO inst range input filter or place constants using min and max hue
        # TODO implement filter that iterates between the hue boundries using the speed as a fraction for the time input
        #  this should be repeated with the configured phase offset for every desired fragment
        fragment_outputs = []
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
        self._number_of_fragments = min(new_fragment_count, 1)

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
        return {"type": self.EFFECT_ID,
                "number-of-fragments": self._number_of_fragments,
                "min-hue": self._min_hue,
                "max-hue": self._max_hue,
                "default-speed": self._default_speed}
        # TODO implement recurse into slots if they're occupied

    def deserialize(self, data: dict[str, str]):
        self._number_of_fragments = data['number-of-fragments']
        self._min_hue = data["min-hue"]
        self._max_hue = data["max-hue"]
        self._default_speed = data["default-speed"]
        self._widget.load_values_from_effect()
