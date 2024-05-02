from abc import ABC

from PySide6.QtWidgets import QWidget, QLabel

from model import Filter
from model.curve_configuration import CurveConfiguration
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from view.utility_widgets.curve_editor import CurveEditorWidget


class GenericEffect(Effect, ABC):
    def get_output_slot_type(self):
        return EffectType.GENERIC_NUMBER


class FunctionEffect(GenericEffect):

    def serialize(self) -> dict:
        return {"type": "generic.function",
                "config": self._widget.get_wave_config().serialize()}

    EFFECT_ID = "effect.animation.trigonometric_function"

    def get_serializable_effect_name(self) -> str:
        return self.EFFECT_ID

    def get_configuration_widget(self) -> QWidget | None:
        return self._widget

    def resolve_input_port_name(self, slot_id: str) -> str:
        return "TODO implement"

    def emplace_filter(self, filter_list: list[Filter], prefix: str) -> dict[str, str | list[str]]:
        return dict()

    def __init__(self):
        super().__init__({"phase": [EffectType.GENERIC_NUMBER]})
        self._widget: CurveEditorWidget = CurveEditorWidget()
        self._widget.set_wave_config(CurveConfiguration())

    def get_human_filter_name(self):
        return "Function"

    def get_description(self):
        return "This effect creates wave forms that it follows."

    def deserialize(self, data: dict[str, str]):
        pass  # TODO implement
        new_config = CurveConfiguration.from_str(data.get("config"))
        self._widget.set_wave_config(new_config)
