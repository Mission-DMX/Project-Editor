from abc import ABC

from PySide6.QtWidgets import QWidget

from model import Filter
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
        return {"color": []}

    def get_human_filter_name(self):
        return "Color Wheel"

    def get_description(self):
        return "This effect cycles through a color wheel"

    @property
    def fragment_number(self) -> int:
        return self._number_of_fragments

    @fragment_number.setter
    def fragment_number(self, new_fragment_count: int):
        self._number_of_fragments = new_fragment_count

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
