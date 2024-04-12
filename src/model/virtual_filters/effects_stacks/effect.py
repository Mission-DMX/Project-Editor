from abc import ABC, abstractmethod
from collections.abc import dict_items
from enum import IntFlag

from PySide6.QtWidgets import QWidget

from model import Filter


class EffectType(IntFlag):

    COLOR = 0,
    LIGHT_INTENSITY = 1,
    ENABLED_SEGMENTS = 2,
    PAN_TILT_COORDINATES = 3,
    POSITION_3D = 4,
    SPEED = 5,
    SHUTTER_STROBE = 6,
    GOBO_SELECTION = 7,
    ZOOM_FOCUS = 8,
    GENERIC_NUMBER = 9,

    @property
    def human_readable_name(self) -> str:
        match self:
            case EffectType.COLOR:
                return "Color"
            case EffectType.LIGHT_INTENSITY:
                return "Light Intensity"
            case EffectType.ZOOM_FOCUS:
                return "Zoom and Focus"
            case EffectType.ENABLED_SEGMENTS:
                return "Enabled Lamp Segements"
            case EffectType.PAN_TILT_COORDINATES:
                return "Pan / Tilt"
            case EffectType.POSITION_3D:
                return "3D Coordinates"
            case EffectType.SPEED:
                return "Movement Speed"
            case EffectType.SHUTTER_STROBE:
                return "Shutter"
            case EffectType.GOBO_SELECTION:
                return "Gobo"
            case EffectType.GENERIC_NUMBER:
                return "Number"


class Effect(ABC):

    def __init__(self):
        super().__init__()
        self._inputs: dict[str, "Effect"] = dict()

    @abstractmethod
    def generate_configuration_widget(self) -> QWidget | None:
        """
        This method may to return a configuration widget that may be displayed inside the effect block.

        :returns: the procured widget or none
        """
        raise NotImplementedError()

    @abstractmethod
    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        """
        This method will be queried in order to fetch the sockets together with their list of accepted data types.

        :returns: A dictionary. The keys encode the input ids. The values are a list of accepted input types.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_slot_type(self) -> EffectType:
        """This method needs to return the slot that this effect provides.
        :returns: The EffectType that this effect imposes"""
        raise NotImplementedError()

    @abstractmethod
    def resolve_input_port_name(self, slot_id: str) -> str:
        """
        This method is called in order to resolve human-readable names for the given input slot.

        :param slot_id: The slot id to resolve the name for
        :returns: The human-readable name of the slot
        """
        raise NotImplementedError()

    @abstractmethod
    def emplace_filter(self, heading_effects: dict[str, tuple["Effect", int]], filter_list: list[Filter]):
        """
        This method gets called in order to generate the filters. This method needs to accept the case that an input
        slot is not occupied and needs to emplace reasonable defaults in that case.

        :param heading_effects: For every connected input slot there may be a previous effect that should be input into
        this slot. The string identifies the slot. The second parameter of the provided tuple defines the output slot of
        the filter to use.
        :param filter_list: The list to place the filters in.
        """
        raise NotImplementedError()

    def get_human_filter_name(self) -> str:
        """This method is used in order to retrieve a human-readable name of the effect"""
        return self.__name__

    @abstractmethod
    def get_serializable_effect_name(self) -> str:
        """
        This method needs to be implemented in order to obtain an effect name that can be used to store and recover the
        effects state.

        :returns: A unique identifier for the effect
        """
        raise NotImplementedError()

    def get_description(self) -> str:
        """This method may be used in order to return a human-readable description of the effect"""
        return ""

    @classmethod
    def can_convert_slot(cls, candidate: EffectType, target: EffectType) -> bool:
        if candidate == target:
            return True
        if candidate == EffectType.GENERIC_NUMBER and target in [EffectType.LIGHT_INTENSITY, EffectType.GOBO_SELECTION, EffectType.ZOOM_FOCUS, EffectType.SHUTTER_STROBE]:
            return True
        # TODO add more capabilities once adapters are implemented
        return False

    def attached_inputs(self) -> dict_items[str, "Effect" | None]:
        """This method return the effects that have been added to this effect as an input"""
        return self._inputs.items()

    def attach(self, slot_id: str, e: "Effect") -> bool:
        if e.get_slot_type() not in self.get_accepted_input_types():
            return False
        self._inputs[slot_id] = e
        return True
