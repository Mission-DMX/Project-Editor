from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem

from model import Scene, BoardConfiguration


class ShowBrowser:
    def __init__(self):
        self._widget = QTabWidget()
        self._scene_browsing_tree = QTreeWidget()
        self._universe_browsing_tree = QTreeWidget()
        self._filter_browsing_tree = QTreeWidget()
        self._widget.addTab(self._scene_browsing_tree, QIcon("resources/showbrowser-show.svg"), "Show")
        self._widget.addTab(self._universe_browsing_tree, QIcon("resources/showbrowser-universe.svg"), "Universes")
        self._widget.addTab(self._filter_browsing_tree, QIcon("resources/showbrowser-filterpages.svg"), "Current Scene")

        self._scene_browsing_tree.setColumnCount(1)
        self._universe_browsing_tree.setColumnCount(4)
        self._filter_browsing_tree.setColumnCount(1)

        self._show: BoardConfiguration | None = None
        self._selected_scene: Scene | None = None

        self._refresh_universe_browser()
        self._refresh_scene_browser()

    @property
    def widget(self):
        return self._widget

    @property
    def board_configuration(self) -> BoardConfiguration | None:
        return self._show

    @board_configuration.setter
    def board_configuration(self, b: BoardConfiguration | None):
        self._show = b
        self._refresh_universe_browser()
        self.selected_scene = None

    @property
    def selected_scene(self) -> Scene | None:
        return self._selected_scene

    @selected_scene.setter
    def selected_scene(self, s: Scene | None):
        self._selected_scene = s
        self._refresh_scene_browser()

    def _refresh_universe_browser(self):
        self._universe_browsing_tree.clear()
        i = 0
        for universe in self._show.universes:
            item = QTreeWidgetItem(self._universe_browsing_tree)
            item.setText(0, str(universe.id))
            item.setText(1, str(universe.name))
            item.setText(2, str(universe.location))
            item.setText(3, str(universe.description))
            self._universe_browsing_tree.insertTopLevelItem(i, item)
            for pf in universe.patching:
                fixture_item = QTreeWidgetItem(item)
                fixture_item.setText(0, str(pf.address))
                fixture_item.setText(1, pf.fixture_channel)
                fixture_item.setText(2, pf.fixture.mode)
                fixture_item.setText(3, pf.fixture.name)
            i += 1
        # TODO link with patching update signals

    def _refresh_scene_browser(self):
        pass
