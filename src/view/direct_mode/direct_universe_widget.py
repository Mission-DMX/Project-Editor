# coding=utf-8
"""directly edit channels of a universe"""
from PySide6 import QtWidgets, QtCore

from Style import Style
from model.universe import Universe
from view.direct_mode.channel_widget import ChannelWidget


class DirectUniverseWidget(QtWidgets.QScrollArea):
    """Widget to directly edit channels of one universe.

    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """
    send_universe_value: QtCore.Signal = QtCore.Signal(Universe)

    def __init__(self, universe: Universe, parent=None):
        """Inits a ManualUniverseEditorWidget.

        Args:
            universe: the Universe to edit
            parent: Qt parent of the widget.
        """
        super().__init__(parent=parent)

        self.setFixedHeight(430)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setStyleSheet(Style.SCROLL)

        universe_widget = QtWidgets.QWidget()
        universe_widget.setLayout(QtWidgets.QHBoxLayout(universe_widget))

        # Add all channels of the universe
        for channel in universe.channels:
            channel_widget = ChannelWidget(channel, universe)
            universe_widget.layout().addWidget(channel_widget)
            channel.updated.connect(lambda *args, send_universe=universe: self.send_universe_value.emit(send_universe))

        self.setWidget(universe_widget)
