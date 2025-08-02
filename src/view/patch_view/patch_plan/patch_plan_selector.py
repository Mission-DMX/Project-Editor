"""selector for Patching witch holds all Patching Universes"""
from logging import getLogger
from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QContextMenuEvent
from PySide6.QtWidgets import QScrollArea

from model import BoardConfiguration, Universe
from model.broadcaster import Broadcaster
from model.ofl.fixture import UsedFixture
from view.dialogs.universe_dialog import UniverseDialog
from view.patch_view.patch_plan.patch_plan_widget import PatchPlanWidget

if TYPE_CHECKING:
    from view.patch_view.patch_mode import PatchMode

logger = getLogger(__name__)


class PatchPlanSelector(QtWidgets.QTabWidget):
    """selector for Patching witch holds all Patching Universes"""

    def __init__(self, board_configuration: BoardConfiguration, parent: "PatchMode") -> None:
        super().__init__(parent=parent)
        self._board_configuration = board_configuration
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

    def _add_fixture(self, fixture: UsedFixture) -> None:
        widget: PatchPlanWidget = self._patch_planes[fixture.parent_universe]
        widget.add_fixture(fixture)

    def _generate_universe(self) -> None:
        """add a new Universe to universe Selector"""

        dialog = UniverseDialog(self._board_configuration.next_universe_id(), self)
        if dialog.exec():
            Universe(dialog.output)

    @override
    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """context menu"""
        for index in range(self.tabBar().count() - 1):
            if self.tabBar().tabRect(index).contains(event.pos()):
                menu = QtWidgets.QMenu(self)

                rename_universe = QtGui.QAction("rename Universe", self)
                # delete_scene = QtGui.QAction('delete Scene', self)
                rename_universe.triggered.connect(lambda index_=index: self._rename_universe(index_))
                # delete_scene.triggered.connect(lambda: self._remove_scene(index))
                menu.addAction(rename_universe)
                # menu.addAction(delete_scene)
                menu.popup(QtGui.QCursor.pos())
                break

    def _rename_universe(self, index: int) -> None:
        universe_id = list(self._patch_planes.keys())[index]
        dialog = UniverseDialog(self._board_configuration.universe(universe_id).universe_proto, self)
        if dialog.exec():
            self._board_configuration.universe(universe_id).universe_proto = dialog.output
            self._broadcaster.send_universe.emit(self._board_configuration.universe(index))

    def _add_universe(self, universe: Universe) -> None:
        index = self.tabBar().count() - 1
        patch_plan = QScrollArea()
        patch_plan.setWidgetResizable(True)
        patch_plan.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        patch_plan.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        widget = PatchPlanWidget()
        patch_plan.setWidget(widget)
        self._patch_planes.update({universe.id: widget})
        self.insertTab(index, patch_plan, str(universe.name))

    def _remove_universe(self, universe: Universe) -> None:
        del self._patch_planes[universe.id]
        self.removeTab(universe.id)
        logger.info("Removing patching tab %s", universe.id)

    def _tab_clicked(self, scene_index: int) -> None:
        if scene_index == self.tabBar().count() - 1:
            self._generate_universe()
