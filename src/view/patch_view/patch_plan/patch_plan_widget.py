"""patch Plan Widget for one Universe"""
import math
from typing import override

from PySide6.QtGui import QPainter, QPaintEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import QWidget

from model.ofl.fixture import UsedFixture
from view.patch_view.patch_plan.channel_item_generator import create_item, item_height, item_width
from view.patch_view.patch_plan.used_fixture_widget import UsedFixtureWidget


class PatchPlanWidget(QWidget):
    """Patch Plan Widget for one Universe"""

    def __init__(self) -> None:
        super().__init__()
        self._chanel_items: list[QPixmap] = []
        self._cols = 1
        self._init_items()
        self._fixtures: list[UsedFixtureWidget] = []

    def _init_items(self) -> None:
        """initiate Channel Items"""
        for i in range(1, 513):
            pixmap = create_item(i)
            self._chanel_items.append(pixmap)

    @override
    def paintEvent(self, _: QPaintEvent) -> None:
        """paint the widget"""
        painter = QPainter(self)
        cols = self.width() // item_width()
        for i, channel_item in enumerate(self._chanel_items):
            x = (i % cols) * item_width()
            y = (i // cols) * item_height()
            painter.drawPixmap(x, y, channel_item)

        for fixture in self._fixtures:
            for i, fixture_channel in enumerate(fixture.pixmap):
                x = ((i + fixture.start_index) % cols) * item_width()
                y = ((i + fixture.start_index) // cols) * item_height()
                painter.drawPixmap(x, y, fixture_channel)

        painter.end()

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        """resize the widget"""
        new_cols = max(1, self.width() // item_width())
        if new_cols != self._cols:
            self._cols = new_cols
            self.update_widget_height()
        super().resizeEvent(event)

    def update_widget_height(self) -> None:
        """update the widget height"""
        rows = math.ceil(512 / self._cols)
        self.setFixedHeight(rows * item_height())

    def add_fixture(self, fixture: UsedFixture) -> None:
        """add a fixture to the widget"""
        new_fixture = UsedFixtureWidget(fixture)
        self._fixtures.append(new_fixture)
        self.update()
