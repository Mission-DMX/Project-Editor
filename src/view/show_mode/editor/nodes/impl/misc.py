"""Contains miscellaneous filter nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.filter import FilterTypeEnumeration
from view.show_mode.editor.nodes import FilterNode

if TYPE_CHECKING:
    from model import Scene
    from model.filter import Filter


class EventSchedulerNode(FilterNode):
    """Filter to schedule events."""

    nodeName = "Event Scheduler"  # noqa: N815

    def __init__(self, model: Filter | Scene, name: str) -> None:
        """Initialize the filter."""
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_EVENT_SCHEDULER, name=name)
