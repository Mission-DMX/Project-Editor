# coding=utf-8
"""selector for Patching witch holds all Patching Universes"""
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from view.dialogs.universe_dialog import UniverseDialog
from view.patch_view.patch_plan.patch_plan_widget import PatchPlanWidget

if TYPE_CHECKING:
    from view.patch_view.patch_mode import PatchMode


logger = getLogger(__file__)


class PatchPlanSelector(QtWidgets.QTabWidget):
    """selector for Patching witch holds all Patching Universes"""

    def __init__(self, parent: "PatchMode"):
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._broadcaster.add_universe.connect(self._add_universe)
        self._broadcaster.delete_universe.connect(self._remove_universe)
        self._patch_planes: list[PatchPlanWidget] = []
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.addTab(QtWidgets.QWidget(), "+")
        # self.currentChanged.connect(self._tab_changed)
        self.tabBarClicked.connect(self._tab_clicked)
        self.tabBar().setCurrentIndex(0)

    def _generate_universe(self) -> None:
        """add a new Universe to universe Selector"""
        dialog = UniverseDialog(len(self._broadcaster.patching_universes) + 1)
        if dialog.exec():
            universe = PatchingUniverse(dialog.output)
            self._broadcaster.add_universe.emit(universe)

    def contextMenuEvent(self, event):
        """context menu"""
        for index in range(self.tabBar().count() - 1):
            if self.tabBar().tabRect(index).contains(event.pos()):
                menu = QtWidgets.QMenu(self)

                rename_universe = QtGui.QAction('rename Universe', self)
                # delete_scene = QtGui.QAction('delete Scene', self)
                rename_universe.triggered.connect(lambda: self._rename_universe(index))
                # delete_scene.triggered.connect(lambda: self._remove_scene(index))
                menu.addAction(rename_universe)
                # menu.addAction(delete_scene)
                menu.popup(QtGui.QCursor.pos())
                break

    def _rename_universe(self, index: int) -> None:
        dialog = UniverseDialog(self._broadcaster.patching_universes[index].universe_proto)
        if dialog.exec():
            self._broadcaster.patching_universes[index].universe_proto = dialog.output
            self._broadcaster.send_universe.emit(self._broadcaster.patching_universes[index])

    def _add_universe(self, universe: PatchingUniverse):
        index = self.tabBar().count() - 1
        patch_plan = PatchPlanWidget(universe, parent=self)
        self._patch_planes.append(patch_plan)
        self.insertTab(index, patch_plan, str(universe.universe_proto.id))

    def _remove_universe(self, universe: PatchingUniverse):
        to_remove = []
        for ppu in self._patch_planes:
            if ppu.universe.universe_proto.id == universe.universe_proto.id:
                to_remove.append(ppu)
        for tr in to_remove:
            index = self.indexOf(tr)
            self.removeTab(index)
            logger.info(f"Removing patching tab {index}")
            self._patch_planes.remove(tr)

    def _tab_clicked(self, scene_index: int) -> None:
        if scene_index == self.tabBar().count() - 1:
            self._generate_universe()
