"""Contains miscullaneus filter nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter import FilterTypeEnumeration

from view.show_mode.editor.nodes import FilterNode

if TYPE_CHECKING:
    from model.filter import Filter
    from model import Scene

class EventSchedulerNode(FilterNode):
    """Filter to schedule events."""

    nodeName = "Event Scheduler"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        """Initialize the filter"""
        super().__init__(
            model=model,
            filter_type=FilterTypeEnumeration.FILTER_EVENT_SCHEDULER,
            name=name
        )
        # TODO setup GUI for recommended trigger event types, default trigger event type and event data list
        if "event_data" not in self.filter.filter_configurations.keys():
            self.filter.filter_configurations["event_data"] = ""
        parameter_keys = self.filter.initial_parameters.keys()
        for entry, default_val in [("length", "0"), ("update_triggers", ""), ("step", "0"), ("synchronization_target", "0,0")]:
            if entry in parameter_keys:
                self.filter.initial_parameters[entry] = default_val