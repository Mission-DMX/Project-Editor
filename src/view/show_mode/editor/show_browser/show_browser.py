from typing import Optional, List

import proto.UniverseControl_pb2

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QToolBar, QMenu

from model import Scene, BoardConfiguration, Device
from model.scene import FilterPage
from ofl.fixture import UsedFixture

from .annotated_item import AnnotatedTreeWidgetItem
from .fixture_to_filter import place_fixture_filters_in_scene
from ..editing_utils import add_scene_to_show
from ..scenetab import SceneTabWidget


class ShowBrowser:

    _filter_icon = QIcon("resources/filter.svg")
    _scene_browser_tab_icon = QIcon("resources/showbrowser-show.svg")
    _universe_browser_tab_icon = QIcon("resources/showbrowser-universe.svg")
    _filter_browser_tab_icon = QIcon("resources/showbrowser-filterpages.svg")

    def __init__(self, parent: QWidget, show: BoardConfiguration, editor_tab_browser: QTabWidget):
        self._widget = QWidget(parent)
        self._widget.setMaximumWidth(450)
        self._widget.setMinimumWidth(250)
        self._tab_widget = QTabWidget()
        self._scene_browsing_tree = QTreeWidget()
        self._universe_browsing_tree = QTreeWidget()
        self._filter_browsing_tree = QTreeWidget()
        self._tab_widget.addTab(self._scene_browsing_tree, ShowBrowser._scene_browser_tab_icon, "Show")
        self._tab_widget.addTab(self._universe_browsing_tree, ShowBrowser._universe_browser_tab_icon, "Universes")
        self._tab_widget.addTab(self._filter_browsing_tree, ShowBrowser._filter_browser_tab_icon, "Current Scene")

        self._scene_browsing_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._scene_browsing_tree.customContextMenuRequested.connect(self._scene_context_menu_triggered)
        self._scene_browsing_tree.itemDoubleClicked.connect(self._scene_item_double_clicked)

        self._universe_browsing_tree.itemDoubleClicked.connect(self._universe_item_double_clicked)

        self._scene_browsing_tree.setColumnCount(2)
        self._universe_browsing_tree.setColumnCount(4)
        self._filter_browsing_tree.setColumnCount(1)

        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Element", lambda: self._add_element_pressed())
        self._tool_bar.addAction(QIcon.fromTheme("document-properties"), "Edit", lambda: self._edit_element_pressed())
        self._tool_bar.addAction(QIcon.fromTheme("view-refresh"), "Refresh", lambda: self._refresh_all())

        layout = QVBoxLayout()
        layout.addWidget(self._tool_bar)
        layout.addWidget(self._tab_widget)
        self._widget.setLayout(layout)

        self._editor_tab_widget = editor_tab_browser
        self._show: BoardConfiguration | None = None
        self._selected_scene: Scene | None = None
        if show:
            self.board_configuration = show

    def _refresh_all(self):
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
        if not self._show and b:
            b.broadcaster.add_universe.connect(lambda: self._refresh_universe_browser())
            b.broadcaster.delete_universe.connect(lambda: self._refresh_universe_browser())
            # TODO listen to scene delete signal
            b.broadcaster.fixture_patched.connect(lambda: self._refresh_universe_browser())
        self._show = b
        self._refresh_all()
        self.selected_scene = None

    @property
    def selected_scene(self) -> Scene | None:
        return self._selected_scene

    @selected_scene.setter
    def selected_scene(self, s: Scene | None):
        self._selected_scene = s
        self._refresh_filter_browser()

    def _refresh_universe_browser(self):

        def location_to_string(location):
            if isinstance(location, proto.UniverseControl_pb2.Universe.ArtNet):
                return "{}:{}/{}".format(location.ip_address, location.port, location.universe_on_device)
            elif isinstance(location, proto.UniverseControl_pb2.Universe.USBConfig):
                return "USB:{}".format(location.serial)
            elif isinstance(location, int):
                return "local/{}".format(location)
            else:
                return str(location)

        self._universe_browsing_tree.clear()
        i = 0
        if self._show:
            for universe in self._show.universes:
                item = AnnotatedTreeWidgetItem(self._universe_browsing_tree)
                item.setText(0, str(universe.id))
                item.setText(1, str(universe.name))
                item.setText(2, location_to_string(universe.location))
                item.setText(3, str(universe.description))
                item.setExpanded(True)
                item.annotated_data = universe
                self._universe_browsing_tree.insertTopLevelItem(i, item)
                placed_fixtures = set()
                last_fixture_object: AnnotatedTreeWidgetItem | None = None
                for patching_channel in universe.patching:
                    channel_fixture = patching_channel.fixture
                    if not channel_fixture.is_placeholder and (channel_fixture not in placed_fixtures
                                                               or last_fixture_object is None):
                        last_fixture_object = AnnotatedTreeWidgetItem(item)
                        last_fixture_object.setText(0, "{}/{}".format(universe.id, patching_channel.address + 1))
                        last_fixture_object.setText(1, channel_fixture.name)
                        last_fixture_object.setText(2, str(channel_fixture.mode))
                        last_fixture_object.setText(3, channel_fixture.comment)
                        last_fixture_object.annotated_data = channel_fixture
                        placed_fixtures.add(channel_fixture)
                    if not channel_fixture.is_placeholder:
                        channel_item = AnnotatedTreeWidgetItem(last_fixture_object)
                        channel_item.setText(0, "{}/{}".format(universe.id, patching_channel.address + 1))
                        channel_item.setText(1, patching_channel.fixture_channel)
                        channel_item.setText(2, str(channel_fixture.mode))
                        channel_item.setText(3, channel_fixture.name)
                        channel_item.annotated_data = patching_channel
                i += 1

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
        def add_filter_page(parent_item: AnnotatedTreeWidgetItem, fp: FilterPage):
            filter_page_item = AnnotatedTreeWidgetItem(parent_item)
            filter_page_item.setText(0, fp.name)
            filter_page_item.setText(1, str(len(fp.filters)) + " Filters")
            filter_page_item.annotated_data = fp
            for fp_child in fp.child_pages:
                add_filter_page(filter_page_item, fp_child)
        item = AnnotatedTreeWidgetItem(self._scene_browsing_tree)
        item.setText(0, str(s.scene_id))
        item.setText(1, str(s.human_readable_name))
        item.annotated_data = s
        for fp in s.pages:
            add_filter_page(item, fp)
        self._scene_browsing_tree.insertTopLevelItem(self._scene_browsing_tree.topLevelItemCount(), item)

    def _refresh_scene_browser(self):
        self._scene_browsing_tree.clear()
        if self._show:
            for scene in self._show.scenes:
                self._add_scene_to_scene_browser(scene)

    def _add_element_pressed(self):
        new_scene = add_scene_to_show(self._widget, self._show)
        if new_scene:
            self._add_scene_to_scene_browser(new_scene)

    def _edit_element_pressed(self):
        pass

    def _scene_context_menu_triggered(self, point: QPoint):
        selected_items = self._scene_browsing_tree.selectedItems()

        has_scenes = False

        for si in selected_items:
            if isinstance(si, AnnotatedTreeWidgetItem):
                if isinstance(si.annotated_data, Scene):
                    has_scenes = True

        menu = QMenu(self._scene_browsing_tree)
        pos = self._widget.pos()
        menu.setGeometry(pos.x() + point.x(), pos.y() + point.y(), 100, 200)
        if has_scenes:
            menu.addAction(QIcon.fromTheme("edit-delete"), "Delete", lambda: self._delete_scenes_from_context_menu(selected_items))
        menu.show()

    def _delete_scenes_from_context_menu(self, items: List[AnnotatedTreeWidgetItem]):
        for si in items:
            if isinstance(si, AnnotatedTreeWidgetItem):
                if isinstance(si.annotated_data, Scene):
                    scene_to_delete = si.annotated_data
                    self._show.broadcaster.delete_scene.emit(scene_to_delete)
                    del si
        self._refresh_scene_browser()

    def _scene_item_double_clicked(self, item):
        if isinstance(item, AnnotatedTreeWidgetItem):
            data = item.annotated_data
            if isinstance(data, Scene):
                self._show.broadcaster.scene_open_in_editor_requested.emit(data)

    def _universe_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        if isinstance(item.annotated_data, UsedFixture):
            current_widget = self._editor_tab_widget.currentWidget()
            if isinstance(current_widget, SceneTabWidget):
                # TODO distinguish filter pages once implemented
                if place_fixture_filters_in_scene(item.annotated_data, current_widget.scene.pages[0]):
                    current_widget.refresh()
                    # TODO notify editor about filter update
