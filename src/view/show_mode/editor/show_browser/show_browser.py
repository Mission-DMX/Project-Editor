from typing import Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QToolBar

from model import Scene, BoardConfiguration, Universe
from model.scene import FilterPage

from .annotated_item import AnnotatedTreeWidgetItem
from ..editing_utils import add_scene_to_show


class ShowBrowser:

    _filter_icon = QIcon("resources/filter.svg")
    _scene_browser_tab_icon = QIcon("resources/showbrowser-show.svg")
    _universe_browser_tab_icon = QIcon("resources/showbrowser-universe.svg")
    _filter_browser_tab_icon = QIcon("resources/showbrowser-filterpages.svg")

    def __init__(self, parent: QWidget, show: Optional[BoardConfiguration] = None):
        self._widget = QWidget(parent)
        self._tab_widget = QTabWidget()
        self._scene_browsing_tree = QTreeWidget()
        self._universe_browsing_tree = QTreeWidget()
        self._filter_browsing_tree = QTreeWidget()
        self._tab_widget.addTab(self._scene_browsing_tree, ShowBrowser._scene_browser_tab_icon, "Show")
        self._tab_widget.addTab(self._universe_browsing_tree, ShowBrowser._universe_browser_tab_icon, "Universes")
        self._tab_widget.addTab(self._filter_browsing_tree, ShowBrowser._filter_browser_tab_icon, "Current Scene")

        self._scene_browsing_tree.setColumnCount(2)
        self._universe_browsing_tree.setColumnCount(4)
        self._filter_browsing_tree.setColumnCount(1)

        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Element", lambda: self._add_element_pressed())
        self._tool_bar.addAction(QIcon.fromTheme("document-properties"), "Edit", lambda: self._edit_element_pressed())

        layout = QVBoxLayout()
        layout.addWidget(self._tool_bar)
        layout.addWidget(self._tab_widget)
        self._widget.setLayout(layout)

        self._show: BoardConfiguration | None = show
        self._selected_scene: Scene | None = None

        self._refresh_scene_browser()
        self._refresh_universe_browser()
        self._refresh_filter_browser()

    @property
    def widget(self):
        return self._widget

    @property
    def board_configuration(self) -> BoardConfiguration | None:
        return self._show

    @board_configuration.setter
    def board_configuration(self, b: BoardConfiguration | None):
        self._show = b
        self._refresh_scene_browser()
        self._refresh_universe_browser()
        self.selected_scene = None

    @property
    def selected_scene(self) -> Scene | None:
        return self._selected_scene

    @selected_scene.setter
    def selected_scene(self, s: Scene | None):
        self._selected_scene = s
        self._refresh_filter_browser()

    def _refresh_universe_browser(self):
        self._universe_browsing_tree.clear()
        i = 0
        if self._show:
            for universe in self._show.universes:
                item = AnnotatedTreeWidgetItem(self._universe_browsing_tree)
                item.setText(0, str(universe.id))
                item.setText(1, str(universe.name))
                item.setText(2, str(universe.location))
                item.setText(3, str(universe.description))
                item.annotated_data = universe
                self._universe_browsing_tree.insertTopLevelItem(i, item)
                for pf in universe.patching:
                    fixture_item = AnnotatedTreeWidgetItem(item)
                    fixture_item.setText(0, str(pf.address))
                    fixture_item.setText(1, pf.fixture_channel)
                    fixture_item.setText(2, pf.fixture.mode)
                    fixture_item.setText(3, pf.fixture.name)
                    fixture_item.annotated_data = pf
                i += 1
        # TODO link with patching update signals

    def _refresh_filter_browser(self):
        self._filter_browsing_tree.clear()

        def generate_tree_item(fp: FilterPage, parent) -> QTreeWidgetItem:
            item = AnnotatedTreeWidgetItem(parent)
            item.setText(0, fp.name)
            item.annotated_data = fp
            # TODO set icon for page
            for f in fp.filters:
                filter_item = AnnotatedTreeWidgetItem(item)
                filter_item.setText(0, f.filter_id)
                filter_item.setIcon(0, ShowBrowser._filter_icon)
                filter_item.annotated_data = f
            for child_page in fp.child_pages:
                generate_tree_item(child_page, item)
            return item

        i = 0
        if self._selected_scene:
            for page in self._selected_scene.pages:
                tlli = generate_tree_item(page, self._filter_browsing_tree)
                self._filter_browsing_tree.insertTopLevelItem(i, tlli)
                i += 1

    def _add_scene_to_scene_browser(self, s: Scene):
        item = AnnotatedTreeWidgetItem(self._scene_browsing_tree)
        item.setText(0, s.scene_id)
        item.setText(1, s.human_readable_name)
        item.annotated_data = s
        self._scene_browsing_tree.insertTopLevelItem(self._scene_browsing_tree.topLevelItemCount(), item)

    def _refresh_scene_browser(self):
        self._scene_browsing_tree.clear()
        if self._show:
            for scene in self._show.scenes:
                self._add_scene_to_scene_browser(scene)

    def _add_element_pressed(self):
        selected_tab_widget = self._tab_widget.currentWidget()
        if selected_tab_widget == self._scene_browsing_tree:
            new_scene = add_scene_to_show(self._widget, self._show)
            if new_scene:
                self._add_scene_to_scene_browser(new_scene)
        elif selected_tab_widget == self._universe_browsing_tree:
            # TODO add universe
            pass
        else:
            # TODO add filter page
            pass

    def _edit_element_pressed(self):
        pass
