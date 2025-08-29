# pylint: disable=implicit-flag-alias
"""Fundamental building blocks for effects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntFlag
from typing import TYPE_CHECKING, Never, Self

if TYPE_CHECKING:
    from collections.abc import ItemsView

    from PySide6.QtWidgets import QWidget

    from model import Filter, Scene
    from model.virtual_filters.effects_stacks.vfilter import EffectsStack


class EffectType(IntFlag):
    """Enum representing the different effect types.

    An effect type defines the functionality it provides.
    Each effect can only represent one type, but automatic conversion between certain types may be possible.

    Expected behavior per type:

    - **Color**: Outputs a selection of colors.
    - **Light Intensity**: Outputs a single number between 0 and 255 indicating the desired brightness.
    - **Enabled Segments**: Outputs a list of numbers between 0 and 1 indicating the requested lightness
      (e.g., of a pixel segment).
    - **Pan / Tilt Coordinates**: Provides a tuple (or list of tuples) of pan/tilt coordinates for moving fixtures.
    - **Position 3D**: Provides a tuple (or list of tuples) with positions in 3D space defined as (x, y, z).
    - **Speed**: Indicates the speed of effect transitions.
    - **Shutter / Strobe**: Defines stroboscopic speed (frequency in Hz, float) or disables it by setting 0.0.
      A value of 0 means the light output should be continuously enabled.
    - **Gobo Selection**: Indicates the desired gobo. TODO: define a shared database for gobo images
    - **Zoom / Focus**: Provides a tuple (or list of tuples) with numbers between 0 and 1 indicating zoom and focus.
    - **Generic Number**: A generic numeric value usable for miscellaneous purposes.
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
        """Name of the effect type."""
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
        return ""


class Effect(ABC):
    """Abstract Effect."""

    def __init__(self, supported_input_types: dict[str, list[EffectType]]) -> None:
        """Abstract Effect."""
        super().__init__()
        self._supported_inputs = supported_input_types
        self._inputs: dict[str, Effect | None] = {}
        for slot_name in supported_input_types:
            self._inputs[slot_name] = None
        self._parent_filter: EffectsStack | None = None
        self._containing_slot: tuple[Effect, str] | None = None

    @abstractmethod
    def get_configuration_widget(self) -> QWidget | None:
        """Return a configuration widget for display inside the effect block.

        This method may return a widget that can be shown in the effect block.
        Since it may be called frequently, the widget should be cached to avoid unnecessary re-creation.

        Returns:
        The cached or newly created configuration widget, or None if not available.

        """
        raise NotImplementedError

    def get_accepted_input_types(self) -> dict[str, list[EffectType]]:
        """Fetch the sockets together with their accepted data types.

        Returns:
            A dictionary where the keys encode the input IDs and the values are lists of accepted input types.

        """
        return self._supported_inputs

    @abstractmethod
    def get_output_slot_type(self) -> EffectType:
        """Return the slot that this effect provides.

        Returns:
            The EffectType that this effect imposes.

        """
        raise NotImplementedError

    @abstractmethod
    def resolve_input_port_name(self, slot_id: str) -> str:
        """Resolve the human-readable name for the given input slot.

        Args:
            slot_id: The slot id to resolve the name for.

        Returns:
            The human-readable name of the slot.

        """
        raise NotImplementedError

    @abstractmethod
    def emplace_filter(self, filter_list: list[Filter], name_prefix: str) -> dict[str, str | list[str]]:
        """Generate filters and return their output ports.

        This method must handle cases where an input slot is not occupied and insert reasonable defaults.
        Implementers are responsible for calling `emplace_filter` on subsequently placed filters.
        The method returns a dictionary describing the output ports of the emplaced filters relevant for using the output.
        The layout of this dictionary is: {"output-name": "filter_id:channel"}.

        Based on the effect output types, the following outputs need to be provided:

        - EffectType.COLOR -> "color", list of pointers to an output port of type HSIColor. If the value of "color" is
        a list of strings, fixture segments are matched with the outputs, repeating if too few and ignoring extras.
        - EffectType.LIGHT_INTENSITY -> "intensity", pointing to an output port of type 8bit.
        - EffectType.ZOOM_FOCUS -> "zoom", "focus".
        - EffectType.ENABLED_SEGMENTS -> numbered outputs for each segment.
        - EffectType.PAN_TILT_COORDINATES -> "pan", "tilt".
        - EffectType.POSITION_3D -> "x", "y", "z".
        - EffectType.SPEED -> "speed".
        - EffectType.SHUTTER_STROBE -> "shutter".
        - EffectType.GOBO_SELECTION -> "gobo".
        - EffectType.GENERIC_NUMBER -> "x".

        Args:
        filter_list: The list to place the filters in.
        name_prefix: The prefix for filter IDs to ensure uniqueness.

        Returns:
        A dictionary indicating which outputs can be used by the calling instance.

        """
        raise NotImplementedError

    def get_human_filter_name(self) -> str:
        """Name of the effect."""
        return self.__class__.__name__

    @abstractmethod
    def get_serializable_effect_name(self) -> str:
        """Return a unique identifier for the effect.

        This method must be implemented to provide an effect name that can be used to store and recover the effect's state.

        Returns:
            A unique identifier for the effect.

        """
        raise NotImplementedError

    def get_description(self) -> str:
        """Return the description of the effect."""
        return ""

    @classmethod
    def can_convert_slot(cls, candidate: EffectType, target: EffectType) -> bool:
        """Check if the candidate effect type can be converted to the target effect type."""
        if candidate == target:
            return True
        return candidate == EffectType.GENERIC_NUMBER and target in [
            EffectType.LIGHT_INTENSITY,
            EffectType.GOBO_SELECTION,
            EffectType.ZOOM_FOCUS,
            EffectType.SHUTTER_STROBE,
        ]
        # TODO add more capabilities once adapters are implemented

    def slot_definitions(self) -> ItemsView[str, Self | None]:
        """Return the effects added as inputs to this effect, including empty slots."""
        return self._inputs.items()

    def attach(self, slot_id: str, e: Effect) -> bool:
        """Attach an effect to a specified input slot.

        Args:
            slot_id: The slot to populate.
            e: The effect to place inside the slot.

        Returns:
            True if the attachment was successful.

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
        """Return a name for the input slot.

        This method should be overridden by implementing classes. By default, it returns the slot's internal ID.

        Args:
            slot_name: The internal ID of the slot.

        Returns:
            A friendly name for the slot.

        """
        return slot_name

    def get_scene(self) -> Scene | None:
        """Return the scene in which the effect is used.

        Note:
        This method may return None.

        Returns:
        The scene if available, otherwise None.

        """
        if self._parent_filter is None:
            return None
        return self._parent_filter.scene

    def get_position(self) -> tuple[float, float]:
        """Retun the position of the parent filter."""
        if self._parent_filter is None:
            return 0, 0
        return self._parent_filter.pos

    def set_parent_filter(self, f: EffectsStack) -> None:
        """Set the parent filter, which needs to be of type EffectsStack."""
        self._parent_filter = f

    @abstractmethod
    def serialize(self) -> dict:
        """Return a dictionary describing the effect for serialization.

        The dictionary must contain at least the 'type' key indicating the effect.
        Implementing functions are responsible for serializing their input effects.

        Returns:
            A dictionary representing the effect state.

        """
        return {}

    @abstractmethod
    def deserialize(self, data: dict[str, str]) -> Never:
        """Restore the effect from a saved show file.

        This method is called when a show file is loaded. It must restore the effect
        and instantiate all of its input effects.

        Args:
            data: A dictionary representing the effect.

        """
        raise NotImplementedError("The class did not implement the deserialize method.")

    @property
    def slot_parent(self) -> tuple[Effect, str] | None:
        """Parent Slot."""
        return self._containing_slot

    def clear_slot(self, slot_id: str) -> None:
        """Clear the slot with the given ID."""
        if slot_id not in self._inputs:
            raise ValueError(f"This filter does not contain an input slot with id {slot_id}.")
        self._inputs[slot_id] = None
