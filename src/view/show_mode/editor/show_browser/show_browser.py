from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem

from model import Scene, BoardConfiguration
from model.scene import FilterPage


class ShowBrowser:

    _filter_icon = QIcon("resources/filter.svg")
    _scene_browser_tab_icon = QIcon("resources/showbrowser-show.svg")
    _universe_browser_tab_icon = QIcon("resources/showbrowser-universe.svg")
    _filter_browser_tab_icon = QIcon("resources/showbrowser-filterpages.svg")

    def __init__(self):
        self._widget = QTabWidget()
        self._scene_browsing_tree = QTreeWidget()
        self._universe_browsing_tree = QTreeWidget()
        self._filter_browsing_tree = QTreeWidget()
        self._widget.addTab(self._scene_browsing_tree, ShowBrowser._scene_browser_tab_icon, "Show")
        self._widget.addTab(self._universe_browsing_tree, ShowBrowser._universe_browser_tab_icon, "Universes")
        self._widget.addTab(self._filter_browsing_tree, ShowBrowser._filter_browser_tab_icon, "Current Scene")

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
            # TODO introduce object that inherits from QTreeWidgetItem but also stores the associated object
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
        self._filter_browsing_tree.clear()

        def generate_tree_item(fp: FilterPage, parent) -> QTreeWidgetItem:
            item = QTreeWidgetItem(parent)
            item.setText(0, fp.name)
            # TODO set icon for page
            for f in fp.filters:
                filter_item = QTreeWidgetItem(item)
                filter_item.setText(0, f.filter_id)
                filter_item.setIcon(0, ShowBrowser._filter_icon)
            for child_page in fp.child_pages:
                generate_tree_item(child_page, item)
            return item

        i = 0
        if self._selected_scene:
            for page in self._selected_scene.pages:
                tlli = generate_tree_item(page, self._filter_browsing_tree)
                self._filter_browsing_tree.insertTopLevelItem(i, tlli)
                i += 1
