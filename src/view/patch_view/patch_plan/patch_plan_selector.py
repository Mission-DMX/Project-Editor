# coding=utf-8
"""selector for Patching witch holds all Patching Universes"""
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets, QtCore
from PySide6.QtWidgets import QScrollArea

from model import Universe
from model.broadcaster import Broadcaster
from model.ofl.fixture import UsedFixture
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
        self._broadcaster.add_fixture.connect(self._add_fixture)

        self._patch_planes: dict[int, PatchPlanWidget] = {}

        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.addTab(QtWidgets.QWidget(), "+")
        # self.currentChanged.connect(self._tab_changed)
        self.tabBarClicked.connect(self._tab_clicked)
        self.tabBar().setCurrentIndex(0)

    def _add_fixture(self, fixture: UsedFixture):
        widget: PatchPlanWidget = self._patch_planes[fixture.parent_universe]
        widget.add_fixture(fixture)

    def _generate_universe(self) -> None:
        """add a new Universe to universe Selector"""
        nex_id = len(self._broadcaster.universes)
        while self._broadcaster.universes.get(nex_id):
            nex_id += 1

        dialog = UniverseDialog(nex_id)
        if dialog.exec():
            universe = Universe(dialog.output)
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
        universe_id = list(self._patch_planes.keys())[index]
        dialog = UniverseDialog(self._broadcaster.universes[universe_id].universe_proto)
        if dialog.exec():
            self._broadcaster.universes[universe_id].universe_proto = dialog.output
            self._broadcaster.send_universe.emit(self._broadcaster.universes[index])

    def _add_universe(self, universe: Universe):
        index = self.tabBar().count() - 1
        patch_plan = QScrollArea()
        patch_plan.setWidgetResizable(True)
        patch_plan.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        patch_plan.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget = PatchPlanWidget()
        patch_plan.setWidget(widget)
        self._patch_planes.update({universe.id: widget})
        self.insertTab(index, patch_plan, str(universe.name))

    def _remove_universe(self, universe: Universe):
        to_remove = []
        for ppu in self._patch_planes:
            if ppu.universe.universe_proto.id == universe.universe_proto.id:
                to_remove.append(ppu)
        for tr in to_remove:
            index = self.indexOf(tr)
            self.removeTab(index)
            logger.info("Removing patching tab %s", index)
            self._patch_planes.remove(tr)

    def _tab_clicked(self, scene_index: int) -> None:
        if scene_index == self.tabBar().count() - 1:
            self._generate_universe()
