"""Module containing vFilter wrapper for fader filters."""
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, override

from model import Filter
from model.control_desk import BankSet, BanksetIDUpdateListener
from model.filter import FilterTypeEnumeration, VirtualFilter

if TYPE_CHECKING:
    from model.scene import Scene

logger = getLogger(__name__)

class FaderUpdatingVFilter(VirtualFilter, BanksetIDUpdateListener):
    """VFilter wrapper to automatically register bank set updates on filter load."""

    def __init__(
            self,
            scene: Scene,
            filter_id: str,
            filter_type: FilterTypeEnumeration,
            pos: tuple[int] | None = None,
    ) -> None:
        """Initialize the filter.

        As this virtual filter simply adds the required callbacks to bank set handling, it behaves much like the
        original filter.

        Args:
            scene: The scene of the filter.
            filter_id: The id of the filter.
            filter_type: The type of the filter. Must be one of the fader ones.
            pos: The position of the filter inside the filter page.

        """
        super().__init__(scene, filter_id, filter_type=int(filter_type), pos=pos)
        self.bankset_model: BankSet | None = None
        self.update_bankset_listener()

    @override
    def resolve_output_port_id(self, virtual_port_id: str) -> str | None:
        return f"{self.filter_id}:{virtual_port_id}"

    @override
    def instantiate_filters(self, filter_list: list[Filter]) -> None:
        f = Filter(self.scene, self.filter_id, FilterTypeEnumeration(self.filter_type * -1),
                   pos=self.pos, filter_configurations=self.filter_configurations.copy(),
                   initial_parameters=self.initial_parameters.copy())
        f.channel_links.update(self.channel_links)
        f.gui_update_keys.update(self.gui_update_keys)
        f.initial_parameters.update(self.initial_parameters)
        f.in_data_types.update(self.in_data_types)
        f.default_values.update(self.default_values)
        filter_list.append(f)

    def update_bankset_listener(self) -> None:
        """Update the attached bank set UUID change listener of this fader."""
        set_id = self.filter_configurations["set_id"]

        if self.scene.linked_bankset.id == set_id:
            self._bankset_model = self.scene.linked_bankset
        else:
            for bs in BankSet.linked_bank_sets():
                if bs.id == set_id:
                    self._bankset_model = bs
                    break
            if self._bankset_model is None:
                column_candidate = self.scene.linked_bankset.get_column(
                    self.filter_configurations.get("column_id"))
                if column_candidate:
                    self.filter_configurations["set_id"] = self.scene.linked_bankset.id
                    self._bankset_model = self.scene.linked_bankset

        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.append(self)

    @override
    def notify_on_new_id(self, new_id: str) -> None:
        logger.debug("New bankset ID: %s", new_id)
        self.filter.filter_configurations["set_id"] = new_id

    def __del__(self) -> None:
        """Deregister the bank set update listener."""
        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.remove(self)
