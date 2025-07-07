"""Patching Mode"""
from logging import getLogger

from PySide6 import QtWidgets

from model import BoardConfiguration, Universe
from view.patch_view.patch_plan.patch_plan_selector import PatchPlanSelector
from view.patch_view.patching.patching_select import PatchingSelect

logger = getLogger(__file__)


class PatchMode(QtWidgets.QStackedWidget):
    """Patching Mode"""

    def __init__(self, board_configuration: BoardConfiguration, parent):
        super().__init__(parent)
        self._board_configuration = board_configuration
        self.addWidget(PatchPlanSelector(board_configuration,self))
        self.addWidget(PatchingSelect(board_configuration, self))
        self._board_configuration.broadcaster.add_universe.connect(self._add_universe)
        self._board_configuration.broadcaster.connection_state_updated.connect(self._connection_changed)
        self._board_configuration.broadcaster.view_to_patch_menu.connect(lambda: self.setCurrentIndex(0))
        self._board_configuration.broadcaster.view_patching.connect(lambda: self.setCurrentIndex(1))
        self._board_configuration.broadcaster.view_leave_patching.connect(lambda: self.setCurrentIndex(0))

    def _add_universe(self, universe: Universe):
        self._board_configuration.broadcaster.send_universe.emit(universe)


    def _connection_changed(self, connected):
        """connection to fish is changed"""
        if connected:
            for universe in self._board_configuration.universes:
                self._board_configuration.broadcaster.send_universe.emit(universe)
