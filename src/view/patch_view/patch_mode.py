# coding=utf-8
"""Patching Mode"""

from PySide6 import QtWidgets, QtGui

from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from view.patch_view.patch_plan.patch_plan_selector import PatchPlanSelector
from view.patch_view.patching.patching_select import PatchingSelect


class PatchMode(QtWidgets.QStackedWidget):
    """Patching Mode"""

    def __init__(self, parent):
        super().__init__(parent)
        self.addWidget(PatchPlanSelector(self))
        self.addWidget(PatchingSelect(self))
        self._broadcaster = Broadcaster()
        self._broadcaster.add_universe.connect(self._add_universe)
        self._broadcaster.connection_state_updated.connect(self._connection_changed)
        self._broadcaster.view_to_patch_menu.connect(lambda: self.setCurrentIndex(0))
        self._broadcaster.view_patching.connect(lambda: self.setCurrentIndex(1))
        self._broadcaster.view_leave_patching.connect(lambda: self.setCurrentIndex(0))

    def _add_universe(self, universe: PatchingUniverse):
        self._broadcaster.patching_universes.append(universe)
        self._broadcaster.send_universe.emit(universe)

    def _connection_changed(self, connected):
        """connection to fish is changed"""
        if connected:
            for universe in self._broadcaster.patching_universes:
                self._broadcaster.send_universe.emit(universe)
