from logging import getLogger

from PySide6.QtWidgets import QWidget

from controller.ofl.fixture import UsedFixture, ColorSupport
from model import Filter
from model.virtual_filters.effects_stacks.color_effects import ColorEffect
from model.virtual_filters.effects_stacks.effect import EffectType, Effect

logger = getLogger(__file__)


class _EffectDummy_Socket(Effect):

    """The purpose of this class is to provide an Effect if required during rendering"""

    def generate_configuration_widget(self) -> QWidget | None:
        return None

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        return {"": [self._stype]}

    def get_output_slot_type(self) -> EffectType:
        return self._stype

    def resolve_input_port_name(self, slot_id: str) -> str:
        return ""

    def emplace_filter(self, heading_effects: dict[str, tuple["Effect", int]], filter_list: list[Filter]):
        pass

    def get_serializable_effect_name(self) -> str:
        raise RuntimeError("A dummy socket is not supposed to be serialized")

    def __init__(self, socket: "EffectsSocket", stype: EffectType):
        super().__init__({"": [stype]})
        self._socket = socket
        self._stype = stype

    def attach(self, slot_id: str, e: "Effect") -> bool:
        if not Effect.can_convert_slot(e.get_output_slot_type(), self._stype):
            return False
        return self._socket.place_effect(e, self._stype)


class EffectsSocket:
    """
    This class contains the anchor for an effect stack on a given group or fixture.
    """

    def __init__(self, target: UsedFixture):
        self.target: UsedFixture = target  # TODO also implement support for fixture groups
        self._color_socket: ColorEffect | None = None
        self.has_color_property: bool = target.check_for_color_property() != ColorSupport.NO_COLOR_SUPPORT

    # TODO implement serialization
    def get_socket_by_type(self, slot_type: EffectType) -> Effect | None:
        if slot_type == EffectType.COLOR and self.has_color_property:
            return self._color_socket
        return None

    def get_socket_or_dummy(self, socket_typ: EffectType) -> Effect:
        if socket_typ == EffectType.COLOR and self._color_socket:
            return self._color_socket
        return _EffectDummy_Socket(self, socket_typ)

    def place_effect(self, e: Effect, target_slot: EffectType) -> bool:
        if not Effect.can_convert_slot(e.get_output_slot_type(), target_slot):
            return False
        if target_slot == EffectType.COLOR and self.has_color_property:
            self._color_socket = e
            return True
        # TODO implement other slot types
        return False
