"""A Used Fixture in the patching view."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, override

from PySide6 import QtWidgets
from PySide6.QtGui import QAction, QColorConstants, QContextMenuEvent, QFont, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

from view.dialogs.fixture_dialog import FixtureDialog
from view.patch_view.patch_plan.channel_item_generator import (
    channel_item_height,
    channel_item_spacing,
    channel_item_width,
    create_item,
)
from view.patch_view.patch_plan.patch_plan_widget import PatchBaseItem

if TYPE_CHECKING:
    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture


class UsedFixtureWidget(PatchBaseItem):
    """UI Widget of a Used Fixture."""

    def __init__(self, fixture: UsedFixture, board_configuration: BoardConfiguration) -> None:
        """UI Widget of a Used Fixture."""
        super().__init__()
        self._fixture: UsedFixture = fixture
        self._board_configuration: BoardConfiguration = board_configuration
        self._shape_path = QPainterPath()
        self._channels_static: list[QPixmap] = []
        fixture.static_data_changed.connect(self._rebild)
        self._rebild()
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    @override
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, /, widget: QWidget | None = ...) -> None:
        x = (self._fixture.start_index % self._cols) * (channel_item_width() + channel_item_spacing())
        y = math.floor(self._fixture.start_index / self._cols) * (channel_item_height() + channel_item_spacing())
        self._shape_path = QPainterPath()
        for channel_item in self._channels_static:
            if x + channel_item_width() > self._view_width:
                x = 0
                y += channel_item_height() + channel_item_spacing()
            painter.drawPixmap(x, y, channel_item)
            self._shape_path.addRect(x, y, channel_item_width(), channel_item_height())
            x += channel_item_width() + channel_item_spacing()

    @override
    def shape(self) -> QPainterPath:
        return self._shape_path

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Context Menu."""
        menu = QtWidgets.QMenu()
        action_modify = QAction("Bearbeiten", menu)

        action_modify.triggered.connect(self._modify_fixture)

        menu.addAction(action_modify)

        menu.exec(event.screenPos())

    def _build_static_pixmap(self, channel_id: int) -> QPixmap:
        """Build Static Pixmap for one Cannel."""
        pixmap = create_item(self._fixture.start_index + channel_id + 1, self._fixture.color_on_stage)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QColorConstants.Black)
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(5, 35, self._fixture.short_name if self._fixture.short_name else self._fixture.name)
        painter.drawText(5, 50, str(self._fixture.get_fixture_channel(channel_id).name))
        painter.drawText(5, 65, str(self._fixture.name_on_stage))
        painter.end()

        return pixmap

    def _rebild(self) -> None:
        """Rebuild all Channel Pixmap's."""
        self._channels_static: list[QPixmap] = []
        for chanel_index in range(self._fixture.channel_length):
            self._channels_static.append(self._build_static_pixmap(chanel_index))
        self.update()

    def _modify_fixture(self) -> None:
        """Modify clicked Fixture."""
        self._dialog = FixtureDialog(self._fixture, self._board_configuration)
        self._dialog.show()
