# coding=utf-8
"""select Universe"""

from PySide6 import QtWidgets

from model import BoardConfiguration
from model.universe import Universe
from view.console_mode.console_universe_widget import DirectUniverseWidget


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""

    def __init__(self, board_configuration: BoardConfiguration, parent) -> None:
        super().__init__(parent=parent)
        self._board_configuration = board_configuration
        self._universes: list[Universe] = []
        self._universe_widgets: list[DirectUniverseWidget] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        if self._board_configuration.universes:
            for universe in self._board_configuration.universes:
                self.add_universe(universe)

    @property
    def universes(self) -> list[Universe]:
        """Universes"""
        return self._universes

    def add_universe(self, universe: Universe) -> None:
        """
        add a new Universe to universe Selector
        Args:
            universe: the new universe to add
        """
        self._board_configuration.broadcaster.send_universe_value.emit(universe)
        self._universes.append(universe)

        widget = QtWidgets.QTabWidget()
        layout = QtWidgets.QVBoxLayout()

        direct_editor: DirectUniverseWidget = DirectUniverseWidget(universe, parent=self)
        layout.addWidget(direct_editor)
        self._universe_widgets.append(direct_editor)

        widget.setLayout(layout)
        self.addTab(widget, str(universe.universe_proto.id))

    def send_all_universe(self) -> None:
        """send all universes to fish"""
        for universe in self._universes:
            self._board_configuration.broadcaster.send_universe_value.emit(universe)

    def notify_activate(self):
        # TODO this obviously breaks given multiple universes but it'll work for now
        for universe_widget in self._universe_widgets:
            universe_widget.notify_activate()
