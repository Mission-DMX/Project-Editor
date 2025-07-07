# pylint: disable=implicit-flag-alias
"""
This file contains the fundamental building blocks for effects.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import ItemsView
from enum import IntFlag
from typing import TYPE_CHECKING, Self

from PySide6.QtWidgets import QWidget

from model import Filter, Scene

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.vfilter import EffectsStack


class EffectType(IntFlag):
    """
    This enum represents the different effect types. An effect type defines the functionality it provides.
    An effect can only ever represent one type, however it is possible to automatically convert between certain types.

    The following behavior is to be expected from effects of the following types:
    Color -- Outputs a selection colors.
    Light Intensity -- Outputs a single number between 0 and 255 indicating the desired brightness
    Enabled Segments -- Outputs a list of numbers between 0 and 1 indicating the requested lightness
                        (for example of a pixel segment)
    Pan / Tilt coordinates -- Provides a tuple (or list of tuples) of pan/tilt coordinates for usage in moving fixtures.
    Position 3D -- provides a tuple or list of tuples indicating positions in 3D space defined by (x,y,z)
    Speed -- Indicates the speed of effect transitions
    Shutter / Strobe -- Defines the stroboscopic speed (as a frequency in Hz [double]) or disables it (by making it
                        0.0). In case of 0 the light output should be continuously enabled.
    Gobo Selection -- Indicates the desired GOBO. TODO: we need to define a shared database for images of gobos in lamps
    Zoom / Focus -- Provides a (list of) tuple(s) of numbers between 0 and 1 indicating the zoom and focus of a fixture.
    Generic number -- A generic number usable for misc purposes.
    """
    COLOR = 0
    LIGHT_INTENSITY = 1
    ENABLED_SEGMENTS = 2
    PAN_TILT_COORDINATES = 3
    POSITION_3D = 4
    SPEED = 5
    SHUTTER_STROBE = 6
    GOBO_SELECTION = 7
    ZOOM_FOCUS = 8
    GENERIC_NUMBER = 9

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

    def __init__(self, supported_input_types: dict[str, list[EffectType]]):
        super().__init__()
        self._supported_inputs = supported_input_types
        self._inputs: dict[str, Effect | None] = {}
        for slot_name in supported_input_types:
            self._inputs[slot_name] = None
        self._parent_filter: EffectsStack | None = None
        self._containing_slot: tuple[Effect, str] | None = None

    @abstractmethod
    def get_configuration_widget(self) -> QWidget | None:
        """
        This method may to return a configuration widget that may be displayed inside the effect block.
        As this method gets called quite often, it is advised that it should cache the widget.

        :returns: the procured widget or none
        """
        raise NotImplementedError()

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        """
        This method will be queried in order to fetch the sockets together with their list of accepted data types.

        :returns: A dictionary. The keys encode the input ids. The values are a list of accepted input types.
        """
        return self._supported_inputs

    @abstractmethod
    def get_output_slot_type(self) -> EffectType:
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
    def emplace_filter(self, filter_list: list[Filter], name_prefix: str) -> dict[str, str | list[str]]:
        """
        This method gets called in order to generate the filters. This method needs to accept the case that an input
        slot is not occupied and needs to emplace reasonable defaults in that case.
        The implementer of this method is responsible for calling into the emplace_filter methods of subsequently
        placed filters. This method needs to return a dictionary describing the output ports of the emplaced filters
        that are relevant for using the output.
        The layout of this dictionary is the following: {"output-name": "filter_id:channel"}

        Based on the effect output types, the following outputs(-names) need to be provided:

        EffectType.COLOR -> "color", (list of) pointers to an output port of type HSIColor. If the value of "color" is
        not a string but an array of string, the segments of the fixture(group) are matched with the provided outputs,
        repeating if there are too few outputs and not using them if there are too many.

        EffectType.LIGHT_INTENSITY -> "intensity", pointing to an output port of type 8bit

        EffectType.ZOOM_FOCUS -> "zoom" (double), "focus" (double)

        EffectType.ENABLED_SEGMENTS -> numbered outputs for each segment of data type double (intensity between 0 and 1)

        EffectType.PAN_TILT_COORDINATES -> "pan" (16bit), "tilt"(16bit)

        EffectType.POSITION_3D -> "x" (double), "y" (double), "z" (double)

        EffectType.SPEED -> "speed" (double); TODO we need to discuss a reasonable unit for this parameter type

        EffectType.SHUTTER_STROBE -> "shutter" (double, frequency in Hz)

        EffectType.GOBO_SELECTION -> "gobo" (int8, number of the selected gobo)

        EffectType.GENERIC_NUMBER -> "x" (double)

        :param filter_list: The list to place the filters in.
        :param name_prefix: The prefix of the filter id that the effect can use. This is to make sure that we're
                            generating unique ids.
        :returns: a dictionary indicating which outputs can be used by the calling instance.
        """
        raise NotImplementedError()

    def get_human_filter_name(self) -> str:
        """This method is used in order to retrieve a human-readable name of the effect"""
        return self.__class__.__name__

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
        return candidate == EffectType.GENERIC_NUMBER and target in [EffectType.LIGHT_INTENSITY,
                                                                     EffectType.GOBO_SELECTION,
                                                                     EffectType.ZOOM_FOCUS, EffectType.SHUTTER_STROBE]
        # TODO add more capabilities once adapters are implemented

    def slot_definitions(self) -> ItemsView[str, Self | None]:
        """This method returns the effects that have been added to this effect as an input as well as empty slots"""
        return self._inputs.items()

    def attach(self, slot_id: str, e: Effect) -> bool:
        """This method gets called in order to attach an effect to an input slot.

        :param slot_id: The slot that should be populated
        :param e: The effect to place inside that slot
        :returns: True if the attachment process was successful.
        """
        target_slot_type = e.get_output_slot_type()
        supported_slot_types = self.get_accepted_input_types()[slot_id]
        found_working = False
        for candidate in supported_slot_types:
            found_working |= Effect.can_convert_slot(target_slot_type, candidate)
        if not found_working:
            return False
        if slot_id not in self._inputs:
            raise ValueError("The requested slot id is not present within this filter.")
        self._inputs[slot_id] = e
        e._containing_slot = (self, slot_id)
        return True

    def get_human_slot_name(self, slot_name: str) -> str:
        """This method provides a human-readable name of the input slot.
        It should be overridden by implementing classes in most cases as it will only return the id by default.

        :param slot_name: The internal id of the slot.
        :returns: A friendly name.
        """
        return slot_name

    def get_scene(self) -> Scene | None:
        """This method returns the scene where the effect is used in.
        Note: this method may return None.

        :returns: The scene (if any)
        """
        if self._parent_filter is None:
            return None
        return self._parent_filter.scene

    def get_position(self) -> tuple[float, float]:
        """Retuns the position of the parent filter."""
        if self._parent_filter is None:
            return 0, 0
        return self._parent_filter.pos

    def set_parent_filter(self, f: EffectsStack):
        """This method sets the parent filter, which needs to be of type EffectsStack."""
        self._parent_filter = f

    @abstractmethod
    def serialize(self) -> dict:
        """This method needs to return a dictionary, containing at least the 'type' key indicating the effect.
        The purpose of this method is to generate a restorable state while saving the show file.
        An implementing function is responsible to call the serialization of its inputs on its own.

        :returns: A dictionary describing the effect."""
        return {}

    @abstractmethod
    def deserialize(self, data: dict[str, str]):
        """This method is called if a show file is being loaded. It needs to be implemented in order to restore the
        effect. It is responsible to instantiate all of its input effects.

        :param data: The representation of the effect as a dictionary.
        """
        raise NotImplementedError("The class did not implement the deserialize method.")

    @property
    def slot_parent(self) -> tuple[Effect, str] | None:
        return self._containing_slot

    def clear_slot(self, slot_id: str):
        if slot_id not in self._inputs:
            raise ValueError(f"This filter does not contain an input slot with id {slot_id}.")
        self._inputs[slot_id] = None
