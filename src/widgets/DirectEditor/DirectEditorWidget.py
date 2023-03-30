from PySide6 import QtWidgets, QtCore

from src.DMXModel import Universe
from .ChannelWidget import ChannelWidget
from src.Style import Style


class DirectEditorWidget(QtWidgets.QTabWidget):
    """Widget to directly edit channels of one or multiple universes.

    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """

    def __init__(self, universes: list[Universe], parent=None):
        """Inits a ManualUniverseEditorWidget.

        Args:
            parent: Qt parent of the widget.
        """
        super().__init__(parent=parent)

        self.setMaximumHeight(420)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        # Tabs left of the content
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        for universe in universes:
            # Scroll area left to right
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll_area.setStyleSheet(Style.SCROLL)

            universe_widget = QtWidgets.QWidget()
            universe_widget.setLayout(QtWidgets.QHBoxLayout(universe_widget))

            # Add all channels of the universe
            for channel in universe.channels:
                universe_widget.layout().addWidget(ChannelWidget(channel, universe))

            scroll_area.setWidget(universe_widget)

            # Add universe with tab name in human-readable form
            self.addTab(scroll_area, str(universe.address + 1))

