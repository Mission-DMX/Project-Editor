from abc import ABC

from PySide6.QtWidgets import QWidget, QLabel

from model import Filter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType


class GenericEffect(Effect, ABC):
    def get_output_slot_type(self):
        return EffectType.GENERIC_NUMBER


class FunctionEffect(GenericEffect):

    EFFECT_ID = "effect.animation.trigonometric_function"

    def get_serializable_effect_name(self) -> str:
        return self.EFFECT_ID

    def get_configuration_widget(self) -> QWidget | None:
        return self._widget

    def resolve_input_port_name(self, slot_id: str) -> str:
        return "TODO implement"

    def emplace_filter(self, filter_list: list[Filter]) -> dict[str, str | list[str]]:
        return dict()

    def __init__(self):
        super().__init__({"phase": [EffectType.GENERIC_NUMBER]})
        self._widget: QWidget = QLabel("Curve editor config widget -- Hier koennte Ihre Werbung stehen")
        # TODO implement curve editor and replace this dummy one with it.

    def get_human_filter_name(self):
        return "Function"

    def get_description(self):
        return "This effect creates wave forms that it follows."
