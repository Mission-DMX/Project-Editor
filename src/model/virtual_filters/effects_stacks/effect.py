from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget

from model import Filter


class Effect(ABC):

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
    def resolve_input_port_name(self, slot_id: str) -> str:
        """
        This method is called in order to resolve human-readable names for the given input slot.

        :param slot_id: The slot id to resolve the name for
        :returns: The human-readable name of the slot
        """
        raise NotImplementedError()

    @abstractmethod
    def emplace_filter(self, heading_effects: dict[str, "Effect"], filter_list: list[Filter]):
        """
        This method gets called in order to generate the filters. This method needs to accept the case that an input
        slot is not occupied and needs to emplace reasonable defaults in that case.

        :param heading_effects: For every connected input slot there may be a previous effect that should be input into
        this slot. The string identifies the slot.
        :param filter_list: The list to place the filters in.
        """
        raise NotImplementedError()
