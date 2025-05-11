# coding=utf-8
"""directly edit channels of a universe"""
from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
from model.control_desk import BankSet
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
        self._universe = universe
        self._broadcaster = Broadcaster()
        self._broadcaster.fixture_patched.connect(self._reload_patched_fixtures)
        self._subwidgets: list[ChannelWidget | QtWidgets.QLabel] = []

        self.setFixedHeight(650)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(Style.SCROLL)

        self._universe_widget = QtWidgets.QWidget()
        self._universe_widget.setLayout(QtWidgets.QHBoxLayout(self._universe_widget))

        # TODO we need to discuss the desired behavior in case of multiple universes in console mode as we may need
        # to switch the active one. For now it is not an issue as we only feature one universe for the theatre play.
        # In future it will be an issue as we intend to use the console as a default for scenes and a scene might use
        # multiple universes.
        self._bank_set = BankSet(gui_controlled=True,
                                 description=f"Console mode Bankset for universe {universe.description}.")
        self._bank_set.activate()
        self._bank_set_control_elements = []

        self._reload_patched_fixtures()

        self.setWidget(self._universe_widget)
        self._broadcaster.jogwheel_rotated_left.connect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.connect(self._increase_scroll)
        self._scroll_position = 0

    def _reload_patched_fixtures(self):
        for w in self._subwidgets:
            self._universe_widget.layout().removeWidget(w)
            w.setParent(None)
            w.deleteLater()
        self._subwidgets.clear()
        # Add all channels of the universe
        for channel, patching_chanel in zip(self._universe.channels, self._universe.patching):
            channel_widget = ChannelWidget(channel, patching_chanel, bank_set=self._bank_set,
                                           bank_set_control_list=self._bank_set_control_elements)
            self._universe_widget.layout().addWidget(channel_widget)
            self._subwidgets.append(channel_widget)

            if patching_chanel.fixture.name != "Empty" and patching_chanel.fixture_channel_id() == len(
                    patching_chanel.fixture.mode['channels']) - 1:
                label = QtWidgets.QLabel(patching_chanel.fixture.name)
                self._universe_widget.layout().addWidget(label)
                self._subwidgets.append(label)

            channel.updated.connect(
                lambda *args, send_universe=self._universe: self._broadcaster.send_universe_value.emit(send_universe))

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

    def automap(self):
        index = 0
        fixtures_per_bank = 0
        for w in self._subwidgets:
            if isinstance(w, ChannelWidget):
                w.notify_automap(index)
                fixtures_per_bank += 1
                if fixtures_per_bank >= 8:
                    index += 1
                    fixtures_per_bank = 0
            else:
                index += 1
                fixtures_per_bank = 0
