"""Typed (prefix, local) channel key used internally by the compile pipeline.

Before S5 the compiler threaded ``f"{prefix}__{local}"`` wire names end-to-end
and re-ran ``str.partition("__")`` wherever the two components were needed
again. That produced the L2 class of bugs: a prefix that happened to contain
``__`` after sanitisation split in the wrong place, and the consolidation
cache keyed on a prefix that shadowed sibling fixtures (L1).

:class:`ChannelKey` makes the two components first-class. Call
:meth:`to_wire_name` once at the serialisation boundary; everywhere else
the tuple fields speak for themselves.
"""

from __future__ import annotations

from typing import NamedTuple

# The wire-name separator between ``prefix`` and ``local``. The sanitiser
# in :func:`model.filters._channel_names.sanitize_channel_name` collapses any
# literal ``__`` in the prefix to ``-`` so the separator is unambiguous.
_SEPARATOR = "__"


class ChannelKey(NamedTuple):
    """Canonical identifier for a vfilter channel.

    ``prefix`` is the sanitised fixture identifier (e.g. ``"Hero_Spot_30ed4259"``),
    ``local`` is the within-property channel name (e.g. ``"brightness_raw"``).
    """

    prefix: str
    local: str

    def to_wire_name(self) -> str:
        """Join ``prefix`` and ``local`` into the wire-name representation."""
        return f"{self.prefix}{_SEPARATOR}{self.local}"


def parse_wire_name(name: str) -> ChannelKey:
    """Split a wire name back into its :class:`ChannelKey` components.

    Relies on the invariant that the sanitiser has removed any ``__`` from the
    prefix (any literal double-underscore collapses to ``-``). The separator
    is therefore unique and ``str.partition`` is deterministic.
    """
    prefix, sep, local = name.partition(_SEPARATOR)
    if not sep:
        # Not a wire name (e.g. a bare canonical that never got a prefix);
        # treat the whole string as the local component.
        return ChannelKey(prefix="", local=prefix)
    return ChannelKey(prefix=prefix, local=local)


def wire_name(prefix: str, local: str) -> str:
    """Return the wire name for the given ``prefix`` / ``local`` pair."""
    return f"{prefix}{_SEPARATOR}{local}"
