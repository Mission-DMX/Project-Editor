# coding=utf-8
"""select Universe"""

from PySide6 import QtWidgets

from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from model.universe import Universe
from view.console_mode.console_universe_widget import DirectUniverseWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog


class UniverseSelector(QtWidgets.QTabWidget):
    """select Universe from Tab Widget"""

    def __init__(self, parent) -> None:
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._universes: list[Universe] = []
        self._universe_widgets: list[DirectUniverseWidget] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        if self._broadcaster.patching_universes:
            for patching_universe in self._broadcaster.patching_universes:
                self.add_universe(patching_universe)

        self._dialog = YesNoDialog(self, self._automap,
                                   text="Would you like to automatically map all channels to bank sets?")

    @property
    def universes(self) -> list[Universe]:
        """Universes"""
        return self._universes

    def add_universe(self, patching_universe: PatchingUniverse) -> None:
        """
        add a new Universe to universe Selector
        Args:
            patching_universe: the new universe to add
        """
        universe = Universe(patching_universe)
        self._broadcaster.send_universe_value.emit(universe)
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
            self._broadcaster.send_universe_value.emit(universe)

    def notify_activate(self):
        # TODO this obviously breaks given multiple universes but it'll work for now
        for universe_widget in self._universe_widgets:
            universe_widget.notify_activate()

    def _automap(self):
        for uw in self._universe_widgets:
            uw.automap()
