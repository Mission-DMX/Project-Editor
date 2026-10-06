"""Reusable mixins for Filter subclasses."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from model.filter import DataType


class StaticIOMixin:
    """Mixin that lets a Filter subclass declare its I/O signature via class attributes.

    Subclasses with a fixed set of input and output terminals declare them once as the ``IN``,
    ``OUT``, ``DEFAULT_VALUES`` and ``GUI_UPDATE_KEYS`` class attributes. The mixin copies
    them into the per-instance dicts whenever :meth:`_rebuild_io` is invoked by
    :class:`model.filter.Filter`. Place this mixin before :class:`~model.filter.Filter` in
    the subclass's base list so that :meth:`_rebuild_io` is resolved to the mixin's version.
    """

    IN: ClassVar[dict[str, DataType]] = {}
    OUT: ClassVar[dict[str, DataType]] = {}
    DEFAULT_VALUES: ClassVar[dict[str, str]] = {}
    GUI_UPDATE_KEYS: ClassVar[dict[str, DataType | list[str]]] = {}

    def _rebuild_io(self) -> None:
        """Copy the declared static I/O signature into the per-instance dicts."""
        self._in_data_types = dict(self.IN)  # type: ignore[attr-defined]
        self._out_data_types = dict(self.OUT)  # type: ignore[attr-defined]
        self._default_values = dict(self.DEFAULT_VALUES)  # type: ignore[attr-defined]
        self._gui_update_keys = dict(self.GUI_UPDATE_KEYS)  # type: ignore[attr-defined]
