"""View, automatically resizes scene."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QGraphicsView

from patch.patch_plan.patch_base_item import PatchBaseItem

if TYPE_CHECKING:
    from PySide6.QtGui import QResizeEvent


class AutoResizeView(QGraphicsView):
    """View, automatically resizes scene."""

    _base_item = PatchBaseItem()

    @override
    def resizeEvent(self, event: QResizeEvent, /) -> None:
        """Resize the View."""
        super().resizeEvent(event)
        new_width = self.viewport().width()
        self._base_item.resize(new_width)
        self.setSceneRect(0, 0, new_width, self._base_item.boundingRect().height())
