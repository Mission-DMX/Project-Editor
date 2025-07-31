"""select Universe"""

from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget

from model import BoardConfiguration
from model.universe import Universe
from view.console_mode.console_universe_widget import DirectUniverseWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""

    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._board_configuration = board_configuration
        board_configuration.broadcaster.add_universe.connect(self.add_universe)
        self._universe_widgets: list[DirectUniverseWidget] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        if self._board_configuration.universes:
            for universe in self._board_configuration.universes:
                self.add_universe(universe)

        self._dialog = YesNoDialog(self, self._automap,
                                   text="Would you like to automatically map all channels to bank sets?")

    def add_universe(self, universe: Universe) -> None:
        """
        add a new Universe to universe Selector
        Args:
            universe: the new universe to add
        """
        widget = QtWidgets.QTabWidget()
        layout = QtWidgets.QVBoxLayout()

        direct_editor: DirectUniverseWidget = DirectUniverseWidget(universe, parent=self)
        layout.addWidget(direct_editor)
        self._universe_widgets.append(direct_editor)

        widget.setLayout(layout)
        self.addTab(widget, str(universe.universe_proto.id))

    def send_all_universe(self) -> None:
        """send all universes to fish"""
        for universe in self._board_configuration.universes:
            self._board_configuration.broadcaster.send_universe_value.emit(universe)

    def notify_activate(self) -> None:
        # TODO this obviously breaks given multiple universes but it'll work for now
        for universe_widget in self._universe_widgets:
            universe_widget.notify_activate()

    def _automap(self):
        for uw in self._universe_widgets:
            uw.automap()
