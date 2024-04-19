from PySide6.QtWidgets import QWidget

from model import Filter
from model.virtual_filters.effects_stacks.effect import EffectType, Effect


class ChainingEffectDummy(Effect):

    """The purpose of this class is to provide an Effect if required during rendering"""

    def serialize(self) -> dict:
        return dict()

    def deserialize(self, data: dict[str, str]):
        pass

    # TODO: we need to replace the two dummy classes with something more suited

    def get_configuration_widget(self) -> QWidget | None:
        return None

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        return {"": self._accepted_input_types}

    def get_output_slot_type(self) -> EffectType:
        return self._effect.get_output_slot_type()

    def resolve_input_port_name(self, slot_id: str) -> str:
        return ""

    def emplace_filter(self, heading_effects: dict[str, tuple[Effect, int]], filter_list: list[Filter]):
        pass

    def get_serializable_effect_name(self) -> str:
        raise RuntimeError("A dummy socket is not supposed to be serialized")

    def __init__(self, e: Effect, socket_name: str, accepted_input_types: list[EffectType]):
        super().__init__({"": accepted_input_types})
        self._effect = e
        self._sname = socket_name
        self._accepted_input_types = accepted_input_types

    def attach(self, slot_id: str, e: "Effect") -> bool:
        return self._effect.attach(slot_id, e)

    def get_human_filter_name(self) -> str:
        return ""
