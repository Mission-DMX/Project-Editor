"""A Used Fixture in the patching view."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction, QColorConstants, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsSceneContextMenuEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

import style
from patch.patch_plan.channel_item_generator import (
    create_item,
    paint_text,
)
from patch.patch_plan.patch_base_item import PatchBaseItem

if TYPE_CHECKING:
    from model.ofl.fixture import UsedFixture


class UsedFixtureView(PatchBaseItem):
    """UI Widget of a Used Fixture."""

    modify_fixture = QtCore.Signal(object)  # UsedFixture

    def __init__(self, fixture: UsedFixture) -> None:
        """UI Widget of a Used Fixture."""
        super().__init__()
        self.setZValue(0)
        self._fixture: UsedFixture = fixture
        self._shape_path = QPainterPath()
        self._channels_static: list[QPixmap] = []
        fixture.static_data_changed.connect(self._rebild)
        self._rebild()
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, /, widget: QWidget | None = ...) -> None:
        """Paint the Used Fixture."""
        x = (self._fixture.start_index % self._cols) * (style.PATCH_ITEM.width + style.PATCH_ITEM.margin)
        y = math.floor(self._fixture.start_index / self._cols) * (style.PATCH_ITEM.height + style.PATCH_ITEM.margin)
        self._shape_path = QPainterPath()
        for channel_item in self._channels_static:
            if x + style.PATCH_ITEM.width > self._view_width:
                x = 0
                y += style.PATCH_ITEM.height + style.PATCH_ITEM.margin
            painter.drawPixmap(x, y, channel_item)
            self._shape_path.addRect(x, y, style.PATCH_ITEM.width, style.PATCH_ITEM.height)
            x += style.PATCH_ITEM.width + style.PATCH_ITEM.margin

    @override
    def shape(self) -> QPainterPath:
        """Clickable Shape."""
        return self._shape_path

    @override
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Context Menu."""
        menu = QtWidgets.QMenu()
        action_modify = QAction("Bearbeiten", menu)

        action_modify.triggered.connect(lambda: self.modify_fixture.emit(self._fixture))

        menu.addAction(action_modify)

        menu.exec(event.screenPos())

    def _build_static_pixmap(self, channel_id: int) -> QPixmap:
        """Build Static Pixmap for one Cannel."""
        pixmap = create_item(self._fixture.start_index + channel_id + 1, self._fixture.color_on_stage)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QColorConstants.Black)
        paint_text(
            painter,
            style.PATCH_ITEM.parts.fixture_name,
            style.PATCH_ITEM.padding,
            self._fixture.short_name if self._fixture.short_name else self._fixture.name,
        )

        paint_text(
            painter,
            style.PATCH_ITEM.parts.fixture_channel_name,
            style.PATCH_ITEM.padding,
            self._fixture.get_fixture_channel(channel_id).name,
        )

        paint_text(
            painter,
            style.PATCH_ITEM.parts.fixture_name_on_stage,
            style.PATCH_ITEM.padding,
            self._fixture.name_on_stage,
        )

        painter.end()

        return pixmap

    def _rebild(self) -> None:
        """Rebuild all Channel Pixmap's."""
        self._channels_static: list[QPixmap] = []
        for chanel_index in range(self._fixture.channel_length):
            self._channels_static.append(self._build_static_pixmap(chanel_index))
        self.update()
