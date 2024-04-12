from abc import ABC

from PySide6.QtWidgets import QWidget

from model import Filter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType


class ColorEffect(Effect, ABC):
    def get_output_slot_type(self):
        return EffectType.COLOR


class ColorWheelEffect(ColorEffect):

    EFFECT_ID = "effect.colors.colorwheel"

    def __init__(self):
        super().__init__({"speed": [EffectType.SPEED],
                          "range": [EffectType.GENERIC_NUMBER]})

    def get_serializable_effect_name(self) -> str:
        return self.EFFECT_ID

    def get_configuration_widget(self) -> QWidget | None:
        # TODO implement
        return None

    def resolve_input_port_name(self, slot_id: str) -> str:
        match slot_id:
            case "speed":
                return "Speed"
            case "range":
                return "Color Range"
        return "Not Implemented"

    def emplace_filter(self, heading_effects: dict[str, tuple["Effect", int]], filter_list: list[Filter]):
        pass

    def get_human_filter_name(self):
        return "Color Wheel"

    def get_description(self):
        return "This effect cycles through a color wheel"
