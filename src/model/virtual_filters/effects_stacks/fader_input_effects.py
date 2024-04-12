from PySide6.QtWidgets import QWidget

from model import Filter
from model.virtual_filters.effects_stacks.color_effects import ColorEffect


class ColorInputEffect(ColorEffect):

    def get_configuration_widget(self) -> QWidget | None:
        pass

    def resolve_input_port_name(self, slot_id: str) -> str:
        pass

    def emplace_filter(self, filter_list: list[Filter]) -> dict[str, str | list[str]]:
        return {}

    def get_serializable_effect_name(self) -> str:
        pass

    def __init__(self):
        super().__init__(dict())
