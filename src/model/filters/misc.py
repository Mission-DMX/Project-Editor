"""Miscellaneous filter subclasses that do not fit another category."""

from __future__ import annotations

from typing import ClassVar

from model.filter import Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter


@register_filter(FilterTypeEnumeration.FILTER_EVENT_SCHEDULER)
class EventScheduler(StaticIOMixin, Filter):
    """Event scheduler filter.

    Config-only filter (no input or output channels); the state lives in the
    ``event_data`` configuration and the ``length``, ``update_triggers``, ``step``, and
    ``synchronization_target`` initial parameters.
    """

    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"event_data": ""}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {
        "length": "0",
        "update_triggers": "",
        "step": "0",
        "synchronization_target": "0,0",
    }
