from abc import ABC

from PySide6.QtWidgets import QWidget

from model import Filter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType


class ColorEffect(Effect, ABC):
    def get_slot_type(self):
        return EffectType.COLOR


class ColorWheelEffect(ColorEffect):

    EFFECT_ID = "effect.colors.colorwheel"

    def get_serializable_effect_name(self) -> str:
        return self.EFFECT_ID

    def generate_configuration_widget(self) -> QWidget | None:
        pass

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        pass

    def resolve_input_port_name(self, slot_id: str) -> str:
        pass

    def emplace_filter(self, heading_effects: dict[str, tuple["Effect", int]], filter_list: list[Filter]):
        pass

    def get_human_filter_name(self):
        return "Color Wheel"

    def get_description(self):
        return "This effect cycles through a color wheel"
