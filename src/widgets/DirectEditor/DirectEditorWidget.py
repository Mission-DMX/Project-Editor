from PySide6 import QtWidgets, QtCore

from Network import NetworkManager
from src.DMXModel import Universe
from .ChannelWidget import ChannelWidget
from src.Style import Style


class DirectEditorWidget(QtWidgets.QScrollArea):
    """Widget to directly edit channels of one or multiple universes.

    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """

    def __init__(self, universe: Universe, fisch_connector: NetworkManager, parent=None):
        """Inits a ManualUniverseEditorWidget.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent=parent)

        self.setFixedHeight(420)

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
            universe_widget.layout().addWidget(ChannelWidget(channel, universe, fisch_connector))

        self.setWidget(universe_widget)
