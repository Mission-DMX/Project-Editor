import json
from logging import getLogger

from PySide6.QtWidgets import QWidget

from controller.ofl.fixture import UsedFixture, ColorSupport
from model import Filter
from model.virtual_filters.effects_stacks.effects.color_effects import ColorEffect
from model.virtual_filters.effects_stacks.effect import EffectType, Effect
from model.virtual_filters.effects_stacks.effect_factory import effect_from_deserialization
from model.virtual_filters.effects_stacks.effects.segment_effects import SegmentEffect

logger = getLogger(__file__)


class _EffectDummy_Socket(Effect):

    """The purpose of this class is to provide an Effect if required during rendering"""

    def serialize(self) -> dict:
        logger.error("A dummy effect should never be serialized. Something went wrong.")
        return {}

    def deserialize(self, data: dict[str, str]):
        pass

    def get_configuration_widget(self) -> QWidget | None:
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

    def get_human_filter_name(self) -> str:
        return ""


class EffectsSocket:
    """
    This class contains the anchor for an effect stack on a given group or fixture.
    """

    def __init__(self, target: UsedFixture):
        self.target: UsedFixture = target  # TODO also implement support for fixture groups
        self._color_socket: ColorEffect | None = None
        self.has_color_property: bool = target.color_support() != ColorSupport.NO_COLOR_SUPPORT
        self._segment_socket: SegmentEffect | None = None
        self.has_segmentation_support: bool = (len(target.red_segments) > 1 and len(target.green_segments) > 1 and
                                               len(target.blue_segments) > 1) or len(target.white_segments) > 1

    # TODO implement serialization
    def get_socket_by_type(self, slot_type: EffectType) -> Effect | None:
        if slot_type == EffectType.COLOR and self.has_color_property:
            return self._color_socket
        if slot_type == EffectType.ENABLED_SEGMENTS and self.has_segmentation_support:
            return self._segment_socket
        # TODO implement other slot types
        return None

    def get_socket_or_dummy(self, socket_typ: EffectType) -> Effect:
        if socket_typ == EffectType.COLOR and self._color_socket:
            return self._color_socket
        if socket_typ == EffectType.ENABLED_SEGMENTS and self._segment_socket:
            return self._segment_socket
        # TODO implement other slot types
        return _EffectDummy_Socket(self, socket_typ)

    def place_effect(self, e: Effect, target_slot: EffectType) -> bool:
        if not Effect.can_convert_slot(e.get_output_slot_type(), target_slot):
            return False
        if target_slot == EffectType.COLOR and self.has_color_property:
            self._color_socket = e
            return True
        elif target_slot == EffectType.ENABLED_SEGMENTS and self.has_segmentation_support:
            self._segment_socket = e
            return True
        # TODO implement other slot types
        return False

    @property
    def is_group(self) -> bool:
        return False  # TODO implement

    def serialize(self) -> str:
        data = {}
        if self._color_socket is not None:
            data["color"] = self._color_socket.serialize()
        if self._segment_socket is not None:
            data["segments"] = self._segment_socket.serialize()
        return json.dumps(data)

    def deserialize(self, data: str):
        data: dict = json.loads(data)
        self._color_socket = None
        self._segment_socket = None
        if self.has_color_property:
            socket_data = data.get("color")
            if socket_data:
                self._color_socket = effect_from_deserialization(socket_data)
        if self.has_segmentation_support:
            socket_data = data.get("segments")
            if socket_data:
                self._segment_socket = effect_from_deserialization(socket_data)
