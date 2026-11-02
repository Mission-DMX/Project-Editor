"""Scripting filter subclasses.

The Lua scripting filter is dynamic-I/O: its terminals come from the semicolon-separated
``in_mapping`` and ``out_mapping`` configuration strings. :meth:`LuaScripting._rebuild_io`
parses them so the filter is fully initialised at construction time.
"""

from __future__ import annotations

from logging import getLogger
from typing import ClassVar

from model.filter import DataType, Filter, FilterTypeEnumeration

from ._mixins import StaticIOMixin
from .factory import register_filter

logger = getLogger(__name__)

_DEFAULT_SCRIPT = """

function update()
    -- This method will be called once per DMX output cycle
    -- Put your effect here
end

function scene_activated()
    -- This method will be called every time the show is switched to this scene
end

"""


@register_filter(FilterTypeEnumeration.FILTER_SCRIPTING_LUA)
class LuaScripting(StaticIOMixin, Filter):
    """Lua scripting filter with configuration-driven input and output channels."""

    DEFAULT_FILTER_CONFIGURATIONS: ClassVar[dict[str, str]] = {"in_mapping": "", "out_mapping": ""}
    DEFAULT_INITIAL_PARAMETERS: ClassVar[dict[str, str]] = {"script": _DEFAULT_SCRIPT}

    def _rebuild_io(self) -> None:
        """Reset I/O to empty, then re-derive it from the ``in_mapping`` / ``out_mapping`` strings."""
        super()._rebuild_io()
        self._parse_mapping(self._filter_configurations.get("in_mapping", ""), self._in_data_types, "input")
        self._parse_mapping(self._filter_configurations.get("out_mapping", ""), self._out_data_types, "output")

    def _parse_mapping(self, mapping: str, target: dict[str, DataType], label: str) -> None:
        """Parse one ``name:dtype;name:dtype`` string, inserting valid entries into ``target``.

        Malformed entries, unknown data types, and duplicates (within either direction or across
        both) are logged and skipped so that a corrupt show file still loads.
        """
        for entry in mapping.split(";"):
            if not entry:
                continue
            name, separator, dtype_str = entry.partition(":")
            if not separator or not name or not dtype_str:
                logger.warning("Lua filter %s: malformed %s mapping entry %r, skipping", self._filter_id, label, entry)
                continue
            if name in self._in_data_types or name in self._out_data_types:
                logger.warning(
                    "Lua filter %s: duplicate channel name %r in %s mapping, skipping", self._filter_id, name, label
                )
                continue
            try:
                target[name] = DataType.from_filter_str(dtype_str)
            except ValueError:
                logger.warning(
                    "Lua filter %s: unknown data type %r for %s channel %r, skipping",
                    self._filter_id,
                    dtype_str,
                    label,
                    name,
                )
