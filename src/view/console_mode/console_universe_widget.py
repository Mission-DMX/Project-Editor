# coding=utf-8
"""directly edit channels of a universe"""
from PySide6 import QtCore, QtWidgets

from model.broadcaster import Broadcaster
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
        broadcaster = Broadcaster()

        self.setFixedHeight(600)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(Style.SCROLL)

        universe_widget = QtWidgets.QWidget()
        universe_widget.setLayout(QtWidgets.QHBoxLayout(universe_widget))

        # Add all channels of the universe
        for channel, patching_chanel in zip(universe.channels, universe.patching):
            channel_widget = ChannelWidget(channel, patching_chanel)
            universe_widget.layout().addWidget(channel_widget)
            channel.updated.connect(
                lambda *args, send_universe=universe: broadcaster.send_universe_value.emit(send_universe))

        self.setWidget(universe_widget)
