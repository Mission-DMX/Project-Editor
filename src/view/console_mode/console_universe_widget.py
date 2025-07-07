"""directly edit channels of a universe"""
from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
from model.control_desk import BankSet
from model.ofl.fixture import UsedFixture
from model.universe import Universe
from style import Style
from view.console_mode.console_channel_widget import ChannelWidget


class DirectUniverseWidget(QtWidgets.QScrollArea):
    """Widget to directly edit channels of one universe.

    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """

    def __init__(self, universe: Universe, parent=None):
        """Inits a ManualUniverseEditorWidget.

        Args:
            universe: the Universe to edit
            parent: Qt parent of the widget.
        """
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._broadcaster.add_fixture.connect(self._add_fixture)
        self._universe = universe

        self.setFixedHeight(650)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(Style.SCROLL)

        self._universe_widget = QtWidgets.QWidget()
        self._universe_widget.setLayout(QtWidgets.QHBoxLayout(self._universe_widget))
        self._universe_widget.layout().setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        self._universe_widget.setFixedHeight(650)
        self._universe_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)

        self._universe_widget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum,
                                            QtWidgets.QSizePolicy.Policy.Expanding)

        self._bank_set = BankSet(gui_controlled=True,
                                 description=f"Console mode Bankset for universe {universe.description}.")
        self._bank_set.activate()
        self._bank_set_control_elements = []

        self.setWidget(self._universe_widget)
        self._universe_widget = self._universe_widget
        self._broadcaster.jogwheel_rotated_left.connect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.connect(self._increase_scroll)
        self._scroll_position = 0

    def __del__(self):
        self._bank_set.unlink()
        self._broadcaster.jogwheel_rotated_left.disconnect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.disconnect(self._increase_scroll)

    def _translate_scroll_position(self, absolute_position):
        # FIXME scrollbars are always strange and clearly more rules apply here
        maximum = self.horizontalScrollBar().maximum()
        widget_width = self._universe_widget.width()
        return (absolute_position / widget_width) * maximum

    def _decrease_scroll(self):
        if self._translate_scroll_position(self._scroll_position - 25) < self.horizontalScrollBar().minimum():
            return
        self._scroll_position -= 25
        self._universe_widget.scroll(25, 0)
        self.horizontalScrollBar().setValue(self._translate_scroll_position(self._scroll_position))

    def _increase_scroll(self):
        if self._translate_scroll_position(self._scroll_position + 25) > self.horizontalScrollBar().maximum():
            return
        self._scroll_position += 25
        self._universe_widget.scroll(-25, 0)
        self.horizontalScrollBar().setValue(self._translate_scroll_position(self._scroll_position))

    def notify_activate(self):
        if self._bank_set:
            self._bank_set.activate()
            self._bank_set.update()  # FIXME activate should suffice
            self._bank_set.push_messages_now()

    def _add_fixture(self, fixture: UsedFixture):
        layout = self._universe_widget.layout()
        for channel_index in range(fixture.channel_length):
            channel_widget = ChannelWidget(fixture.get_fixture_channel(channel_index),
                                           self._universe.channels[fixture.start_index + channel_index],
                                           self._bank_set,
                                           self._bank_set_control_elements, self)
            layout.addWidget(channel_widget)
            self._universe.channels[fixture.start_index + channel_index].updated.connect(
                lambda *args, send_universe=self._universe: self._broadcaster.send_universe_value.emit(send_universe))
        layout.addWidget(QtWidgets.QLabel(fixture.name))
