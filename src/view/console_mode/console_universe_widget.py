# coding=utf-8
"""directly edit channels of a universe"""
from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
from model.control_desk import BankSet
from model.universe import Universe
from Style import Style
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

        self.setFixedHeight(600)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(Style.SCROLL)

        universe_widget = QtWidgets.QWidget()
        universe_widget.setLayout(QtWidgets.QHBoxLayout(universe_widget))

        # TODO we need to discuss the desired behavior in case of multiple universes in console mode as we may need
        # to switch the active one. For now it is not an issue as we only feature one universe for the theatre play.
        # In future it will be an issue as we intend to use the console as a default for scenes and a scene might use
        # multiple universes.
        self._bank_set = BankSet(gui_controlled=True, description="Console mode Bankset for universe {}."
                                 .format(universe.description))
        self._bank_set.activate()
        self._bank_set_control_elements = []

        # Add all channels of the universe
        for channel, patching_chanel in zip(universe.channels, universe.patching):
            channel_widget = ChannelWidget(channel, patching_chanel, bank_set=self._bank_set,
                                           bank_set_control_list=self._bank_set_control_elements)
            universe_widget.layout().addWidget(channel_widget)
            # if last != "Empty" and patching_chanel.fixture_channel == "none":
            if patching_chanel.fixture.name != "Empty" and patching_chanel.fixture_channel_id() == len(
                    patching_chanel.fixture.mode['channels']) - 1:
                universe_widget.layout().addWidget(QtWidgets.QLabel(patching_chanel.fixture.name))
            last = patching_chanel.fixture.name
            channel.updated.connect(
                lambda *args, send_universe=universe: self._broadcaster.send_universe_value.emit(send_universe))

        self.setWidget(universe_widget)
        self._universe_widget = universe_widget
        self._broadcaster.jogwheel_rotated_left.connect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.connect(self._increase_scroll)
        self._scroll_position = 0

    def __del__(self):
        self._bank_set.unlink()
        self._broadcaster.jogwheel_rotated_left.disconnect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.disconnect(self._increase_scroll)

    def _translate_scroll_position(self, absolute_position):
        # FIXME scrollbars are always strange and clearly more rules apply here
        max = self.horizontalScrollBar().maximum()
        widget_width = self._universe_widget.width()
        return (absolute_position / widget_width) * max

    def _increase_scroll(self):
        if self._translate_scroll_position(self._scroll_position - 25) < self.horizontalScrollBar().minimum():
            return
        self._scroll_position -= 25
        self._universe_widget.scroll(25, 0)
        self.horizontalScrollBar().setValue(self._translate_scroll_position(self._scroll_position))

    def _decrease_scroll(self):
        if self._translate_scroll_position(self._scroll_position + 25) > self.horizontalScrollBar().maximum():
            return
        self._scroll_position += 25
        self._universe_widget.scroll(-25, 0)
        self.horizontalScrollBar().setValue(self._translate_scroll_position(self._scroll_position))
