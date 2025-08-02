# coding=utf-8
"""directly edit channels of a universe"""
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QWidget

import style
from model.broadcaster import Broadcaster
from model.control_desk import BankSet
from model.ofl.fixture import UsedFixture
from model.universe import Universe
from view.console_mode.console_channel_widget import ChannelWidget


class DirectUniverseWidget(QtWidgets.QScrollArea):
    """Widget to directly edit channels of one universe.

    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """

    def __init__(self, universe: Universe, parent: QWidget = None) -> None:
        """Inits a ManualUniverseEditorWidget.

        Args:
            universe: the Universe to edit
            parent: Qt parent of the widget.
        """
        super().__init__(parent=parent)
        self._universe = universe
        self._broadcaster = Broadcaster()
        # self._broadcaster.fixture_patched.connect(self._reload_patched_fixtures)
        self._subwidgets: list[ChannelWidget | QtWidgets.QLabel] = []
        self._broadcaster.add_fixture.connect(self._add_fixture)

        self.setFixedHeight(650)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(style.WIDGET)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(style.SCROLL)

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
        self._bank_set_control_elements: list[QWidget] = []

        self.setWidget(self._universe_widget)
        self._broadcaster.jogwheel_rotated_left.connect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.connect(self._increase_scroll)
        self._scroll_position: int = 0

    def __del__(self) -> None:
        self._bank_set.unlink()
        self._broadcaster.jogwheel_rotated_left.disconnect(self._decrease_scroll)
        self._broadcaster.jogwheel_rotated_right.disconnect(self._increase_scroll)

    def _translate_scroll_position(self, absolute_position: int) -> float:
        # FIXME scrollbars are always strange and clearly more rules apply here
        maximum = self.horizontalScrollBar().maximum()
        widget_width = self._universe_widget.width()
        return (absolute_position / widget_width) * maximum

    def _decrease_scroll(self) -> None:
        if self._translate_scroll_position(self._scroll_position - 25) < self.horizontalScrollBar().minimum():
            return
        self._scroll_position -= 25
        self._universe_widget.scroll(25, 0)
        self.horizontalScrollBar().setValue(self._translate_scroll_position(self._scroll_position))

    def _increase_scroll(self) -> None:
        if self._translate_scroll_position(self._scroll_position + 25) > self.horizontalScrollBar().maximum():
            return
        self._scroll_position += 25
        self._universe_widget.scroll(-25, 0)
        self.horizontalScrollBar().setValue(self._translate_scroll_position(self._scroll_position))

    def notify_activate(self) -> None:
        if self._bank_set:
            self._bank_set.activate()
            self._bank_set.update()  # FIXME activate should suffice
            self._bank_set.push_messages_now()

    def automap(self) -> None:
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

    def _add_fixture(self, fixture: UsedFixture) -> None:
        layout = self._universe_widget.layout()
        for channel_index in range(fixture.channel_length):
            channel_widget = ChannelWidget(fixture.get_fixture_channel(channel_index),
                                           self._universe.channels[fixture.start_index + channel_index],
                                           self._bank_set,
                                           self._bank_set_control_elements, self)
            layout.addWidget(channel_widget)
            self._universe.channels[fixture.start_index + channel_index].updated.connect(
                lambda _, send_universe=self._universe: self._broadcaster.send_universe_value.emit(send_universe))
        layout.addWidget(QtWidgets.QLabel(fixture.name))
