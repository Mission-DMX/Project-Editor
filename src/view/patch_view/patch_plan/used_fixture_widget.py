"""A Used Fixture in the patching view"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColorConstants, QFont, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from model.ofl.fixture import UsedFixture
from view.patch_view.patch_plan.channel_item_generator import create_item


class UsedFixtureWidget(QWidget):
    """
    UI Widget of a Used Fixture
    """

    def __init__(self, fixture: UsedFixture) -> None:
        super().__init__()
        self._fixture = fixture
        self._channels_static: list[QPixmap] = []
        fixture.static_data_changed.connect(self._build_static_pixmap)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        for chanel_index in range(fixture.channel_length):
            self._channels_static.append(self._build_static_pixmap(chanel_index))

    @property
    def pixmap(self) -> list[QPixmap]:
        """pixmap of the widget"""
        return self._channels_static

    @property
    def start_index(self) -> int:
        """start index of the fixture"""
        return self._fixture.start_index

    def _build_static_pixmap(self, channel_id: int) -> QPixmap:
        pixmap = create_item(self._fixture.start_index + channel_id + 1, self._fixture.color_on_stage)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QColorConstants.Black)
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(5, 35, str(self._fixture.short_name) if self._fixture.short_name else str(self._fixture.name))
        painter.drawText(5, 50, str(self._fixture.get_fixture_channel(channel_id).name))
        painter.drawText(5, 65, str(self._fixture.name_on_stage))
        painter.end()

        return pixmap
