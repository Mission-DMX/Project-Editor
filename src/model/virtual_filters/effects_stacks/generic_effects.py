from abc import ABC

from PySide6.QtWidgets import QWidget

from model import Filter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType


class GenericEffect(Effect, ABC):
    pass


class FunctionEffect(GenericEffect):
    def generate_configuration_widget(self) -> QWidget | None:
        pass

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        pass

    def resolve_input_port_name(self, slot_id: str) -> str:
        pass

    def emplace_filter(self, heading_effects: dict[str, tuple["Effect", int]], filter_list: list[Filter]):
        pass

    def __init__(self):
        super().__init__()

    def get_human_filter_name(self):
        return "Function"

    def get_description(self):
        return "This effect creates wave forms that it follows."
