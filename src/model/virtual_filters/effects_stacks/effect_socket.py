"""This file provides the effect (dummy) socket classes.
An effect socket provides the inputs for a selected fixture. It is therefore the root of effect chaining.

"""
from __future__ import annotations

import json
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from model import Filter
from model.ofl.fixture import ColorSupport, UsedFixture
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from model.virtual_filters.effects_stacks.effect_factory import effect_from_deserialization
from model.virtual_filters.effects_stacks.effects.color_effects import ColorEffect
from model.virtual_filters.effects_stacks.effects.segment_effects import SegmentEffect

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.vfilter import EffectsStack

logger = getLogger(__name__)


class EffectDummySocket(Effect):
    """The purpose of this class is to provide an Effect if required during rendering"""

    def serialize(self) -> dict:
        logger.error("A dummy effect should never be serialized. Something went wrong.")
        return {}

    def deserialize(self, data: dict[str, str]) -> None:
        pass

    def get_configuration_widget(self) -> QWidget | None:
        return None

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        return {"": [self._stype]}

    def get_output_slot_type(self) -> EffectType:
        return self._stype

    def resolve_input_port_name(self, slot_id: str) -> str:
        return ""

    def emplace_filter(self, heading_effects: dict[str, tuple[Effect, int]], filter_list: list[Filter]) -> None:
        pass

    def get_serializable_effect_name(self) -> str:
        raise RuntimeError("A dummy socket is not supposed to be serialized")

    def __init__(self, socket: EffectsSocket, stype: EffectType) -> None:
        super().__init__({"": [stype]})
        self._socket = socket
        self._stype = stype

    def attach(self, slot_id: str, e: Effect) -> bool:
        if not Effect.can_convert_slot(e.get_output_slot_type(), self._stype):
            return False
        return self._socket.place_effect(e, self._stype)

    def get_human_filter_name(self) -> str:
        return ""


class EffectsSocket:
    """
    This class contains the anchor for an effect stack on a given group or fixture.
    It furthermore proved the entry-point for show file (de)serialization as well as adding of further effects.
    """

    def __init__(self, target: UsedFixture) -> None:
        self.target: UsedFixture = target  # TODO also implement support for fixture groups
        self._color_socket: ColorEffect | None = None
        self.has_color_property: bool = target.color_support != ColorSupport.NO_COLOR_SUPPORT
        self._segment_socket: SegmentEffect | None = None
        self.has_segmentation_support: bool = (target.color_support & ColorSupport.HAS_RGB_SUPPORT > 0 or
                                               target.color_support & ColorSupport.HAS_WHITE_SEGMENT > 0)

    def get_socket_by_type(self, slot_type: EffectType) -> Effect | None:
        """
        get socket by Effect Type
        Args:
            slot_type:

        Returns:

        """
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
        return EffectDummySocket(self, socket_typ)

    def place_effect(self, e: Effect, target_slot: EffectType) -> bool:
        if not Effect.can_convert_slot(e.get_output_slot_type(), target_slot):
            return False

        if target_slot == EffectType.COLOR and self.has_color_property:
            self._color_socket = e
            return True

        if target_slot == EffectType.ENABLED_SEGMENTS and self.has_segmentation_support:
            self._segment_socket = e
            return True
        # TODO implement other slot types
        e._containing_slot = (self, target_slot.name)
        return False

    def clear_slot(self, slot_name: str) -> None:
        match slot_name:
            case _:
                logger.error("Deleting effects from slot name '%s' is not yet implemented.", slot_name)

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

    def deserialize(self, data: str, parent: EffectsStack) -> None:
        data: dict = json.loads(data)
        self._color_socket = None
        self._segment_socket = None
        if self.has_color_property:
            socket_data = data.get("color")
            if socket_data:
                self._color_socket = effect_from_deserialization(socket_data, parent)
        if self.has_segmentation_support:
            socket_data = data.get("segments")
            if socket_data:
                self._segment_socket = effect_from_deserialization(socket_data, parent)
