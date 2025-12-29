"""ShowBrowser widget."""
import os.path
from functools import partial
from typing import cast, Iterable

from flatbuffers.flexbuffers import Object
from PySide6 import QtCore
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QInputDialog, QMenu, QMessageBox, QTabWidget, QToolBar, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget, )

from editor.editor_tab.filter_page.filter_graph.filter_graph_view import FilterGraphWidget, FixtureNode
from model import Scene, UIPage
from model.ofl.fixture import UsedFixture
from src.editor.editor_tab.filter_page.filter_page_tab_view import FilterPageTabWidget
from utility import resource_path
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem
from view.utility_widgets.universe_tree_browser_widget import UniverseTreeBrowserWidget


class ShowBrowserView(QWidget):
    """Provide a navigation bar and browser for the complete show."""

    _filter_icon = QIcon(resource_path(os.path.join("resources", "icons", "filter.svg")))
    _scene_browser_tab_icon = QIcon(resource_path(os.path.join("resources", "icons", "showbrowser-show.svg")))
    _universe_browser_tab_icon = QIcon(resource_path(os.path.join("resources", "icons", "showbrowser-universe.svg")))
    _filter_browser_tab_icon = QIcon(resource_path(os.path.join("resources", "icons", "showbrowser-filterpages.svg")))
    _fader_icon = QIcon(resource_path(os.path.join("resources", "icons", "faders.svg")))
    _uipage_icon = QIcon(resource_path(os.path.join("resources", "icons", "uipage.svg")))

    upload_showfile_clicked = QtCore.Signal()
    add_button_clicked = QtCore.Signal()
    delete_scene = QtCore.Signal(Scene)

    switch_to_tab = QtCore.Signal(Object)

    def __init__(self, parent: QWidget, editor_tab_browser: QTabWidget) -> None:
        """Initialize a ShowBrowser.

        Args:
            parent: The parent Qt widget.
            editor_tab_browser: The editor to use for opening actions.

        """
        super().__init__(parent)
        self.setMaximumWidth(450)
        self.setMinimumWidth(250)
        self._tab_widget = QTabWidget()
        self._scene_browsing_tree = QTreeWidget()
        # self._scene_browsing_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection) #TODO: multiselect notwendig?
        self._universe_browsing_tree = UniverseTreeBrowserWidget()
        self._filter_browsing_tree = QTreeWidget()  # TODO: filter tree
        self._tab_widget.addTab(self._scene_browsing_tree, ShowBrowserView._scene_browser_tab_icon, "Show")
        self._tab_widget.addTab(self._universe_browsing_tree, ShowBrowserView._universe_browser_tab_icon, "Universes")
        self._tab_widget.addTab(self._filter_browsing_tree, ShowBrowserView._filter_browser_tab_icon, "Current Scene")

        self._scene_browsing_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._scene_browsing_tree.customContextMenuRequested.connect(
            self._scene_context_menu_triggered)  # TODO das muss nochmal neu
        self._scene_browsing_tree.itemDoubleClicked.connect(self._scene_item_double_clicked)

        self._universe_browsing_tree.itemDoubleClicked.connect(self._universe_item_double_clicked)

        self._scene_browsing_tree.setColumnCount(2)
        self._filter_browsing_tree.setColumnCount(1)

        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Scene", lambda: self.add_button_clicked.emit())
        self._tool_bar.addAction(QIcon.fromTheme("document-properties"), "Edit", lambda: self._edit_element_pressed())
        self._tool_bar.addAction(QIcon.fromTheme("view-refresh"), "Refresh", lambda: self.refresh_all())
        self._tool_bar.addAction(QIcon.fromTheme("document-send"), "Send showfile to fish",
                                 lambda: self.upload_showfile_clicked.emit())

        self._toolbar_edit_action = self._tool_bar.actions()[1]
        self._toolbar_edit_action.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self._tool_bar)
        layout.addWidget(self._tab_widget)
        self.setLayout(layout)

        self._editor_tab_widget = editor_tab_browser
        self._selected_scene: Scene | None = None

        self._input_dialog = None

    def refresh_all(self) -> None:
        self._refresh_filter_browser()

    @property
    def selected_scene(self) -> Scene | None:
        """Current selected scene."""
        return self._selected_scene

    @selected_scene.setter
    def selected_scene(self, s: Scene | None) -> None:
        self._selected_scene = s
        self._refresh_filter_browser()

    def _refresh_filter_browser(self) -> None:
        pass  # TODO  # self._filter_browsing_tree.clear()  #  # def generate_tree_item(fp: FilterPage, parent: QTreeWidgetItem) -> QTreeWidgetItem:  #     item = AnnotatedTreeWidgetItem(parent)  #     item.setText(0, fp.name)  #     item.annotated_data = fp  #     # TODO set icon for page  #     for f in fp.filters:  #         filter_item = AnnotatedTreeWidgetItem(item)  #         filter_item.setText(0, f.filter_id)  #         filter_item.setIcon(0, ShowBrowserView._filter_icon)  #         filter_item.annotated_data = f  #     # for child_page in fp.child_pages:  #     #    generate_tree_item(child_page, item)  #     return item  #  # i = 0  # if self._selected_scene:  #     for page in self._selected_scene.pages:  #         tlli = generate_tree_item(page, self._filter_browsing_tree)  #         self._filter_browsing_tree.insertTopLevelItem(i, tlli)  #         i += 1

    def add_scene_to_scene_browser(self, s: Scene) -> None:
        """Add a scene to the Show browser."""

        def add_filter_page(parent_item: AnnotatedTreeWidgetItem, fp: FilterGraphWidget) -> None:
            filter_page_item = AnnotatedTreeWidgetItem(parent_item)
            filter_page_item.setText(0, fp.name)
            filter_page_item.setText(1, str(len(fp.filters)) + " Filters")
            filter_page_item.annotated_data = fp

        item = AnnotatedTreeWidgetItem(self._scene_browsing_tree)
        item.setText(0, str(s.scene_id))
        item.setText(1, str(s.human_readable_name))
        item.annotated_data = s
        item.setExpanded(True)
        bankset_item = AnnotatedTreeWidgetItem(item)
        s.ensure_bankset()
        bankset_item.setText(0, "Bankset")
        bankset_item.setIcon(0, ShowBrowserView._fader_icon)
        bankset_item.setText(1, s.linked_bankset.description)
        bankset_item.annotated_data = s.linked_bankset
        if len(s.ui_pages) < 1:
            s.ui_pages.append(UIPage(s))

        for i, ui_page in enumerate(s.ui_pages, start=1):
            uipage_item = AnnotatedTreeWidgetItem(item)
            uipage_item.setText(0, f"UI Page {i} '{ui_page.title}'")
            uipage_item.setIcon(0, ShowBrowserView._uipage_icon)
            uipage_item.setText(1, f"{len(ui_page.widgets)} widgets")
            uipage_item.annotated_data = ui_page
        for fp in s.pages:
            add_filter_page(item, fp)
        self._scene_browsing_tree.insertTopLevelItem(self._scene_browsing_tree.topLevelItemCount(), item)

    def clear_all(self) -> None:
        """clear the Show Browser."""
        self._scene_browsing_tree.clear()
        self._universe_browsing_tree.clear()
        self._filter_browsing_tree.clear()

    def _edit_element_pressed(self) -> None:
        # TODO
        pass

    def _scene_context_menu_triggered(self, point: QPoint) -> None:
        selected_items: list[QTreeWidgetItem] = self._scene_browsing_tree.selectedItems()

        has_scenes = False
        has_filter_pages = False
        has_ui_page = False

        for si in selected_items:
            if isinstance(si, AnnotatedTreeWidgetItem):
                match si.annotated_data:
                    case Scene():
                        has_scenes = True
                    case FilterGraphWidget():
                        has_filter_pages = True
                    case UIPage():
                        has_ui_page = True

        menu = QMenu(self._scene_browsing_tree)
        menu.move(self._scene_browsing_tree.mapToGlobal(point))
        scenes_rename_action = QAction("Rename", menu)
        scenes_rename_action.triggered.connect(lambda: self._rename_scene_from_context_menu(selected_items))
        scenes_rename_action.setEnabled(has_scenes or has_filter_pages or has_ui_page)
        menu.addAction(scenes_rename_action)
        scenes_delete_action = QAction(QIcon.fromTheme("edit-delete"), "Delete", menu)
        scenes_delete_action.triggered.connect(lambda: self._delete_scenes_from_context_menu(selected_items))
        scenes_delete_action.setEnabled(has_scenes)
        menu.addAction(scenes_delete_action)
        menu.addSeparator()
        copy_scene_action = QAction("Duplicate Scene" if len(selected_items) == 1 else "Duplicate Scenes", menu)
        copy_scene_action.triggered.connect(lambda: self._duplicate_scene(selected_items))
        copy_scene_action.setEnabled(has_scenes)
        menu.addAction(copy_scene_action)
        add_filter_page_action = QAction("Add Filter Page", menu)
        add_filter_page_action.triggered.connect(lambda: self._add_filter_page(selected_items))
        add_filter_page_action.setEnabled(has_scenes or has_filter_pages)
        menu.addAction(add_filter_page_action)
        add_ui_page_action = QAction("Add UI page", menu)
        add_ui_page_action.triggered.connect(lambda: self._add_ui_page(selected_items))
        add_ui_page_action.setEnabled(has_scenes)
        menu.addAction(add_ui_page_action)
        menu.show()

    def _delete_scenes_from_context_menu(self, items: list[QTreeWidgetItem]) -> None:
        self._input_dialog = YesNoDialog(self, "Are you sure?",
                                         f"Do you really want to delete the scene {', '.join([f"'{item.text(1)}'" for item in items])}",
                                         partial(self._delete_scenes_from_context_menu_accepted, items),
                                         QMessageBox.Icon.Warning, False, )

    def _delete_scenes_from_context_menu_accepted(self, items: list[AnnotatedTreeWidgetItem]) -> None:
        if self._input_dialog:
            self._input_dialog.close()
            self._input_dialog = None
        for si in items:
            if isinstance(si, AnnotatedTreeWidgetItem) and isinstance(si.annotated_data, Scene):
                scene_to_delete = si.annotated_data
                self.delete_scene.emit(scene_to_delete)
                index = self._scene_browsing_tree.indexOfTopLevelItem(si)
                self._scene_browsing_tree.takeTopLevelItem(index)
                del si

    def _rename_scene_from_context_menu(self, items: list[QTreeWidgetItem]) -> None:
        def rename(c: ShowBrowserView, scene: Scene | FilterGraphWidget, text: str) -> None:
            if isinstance(scene, Scene):
                scene.human_readable_name = text
            if isinstance(scene, UIPage):
                scene.title = text
                self.board_configuration.broadcaster.uipage_renamed.emit(scene.scene.scene_id)
            else:
                scene.name = text
            c._refresh_scene_browser()

        for si in items:
            if isinstance(si, AnnotatedTreeWidgetItem):
                if isinstance(si.annotated_data, Scene):
                    scene_to_rename = si.annotated_data
                    self._input_dialog = QInputDialog(self)
                    self._input_dialog.setInputMode(QInputDialog.TextInput)
                    self._input_dialog.textValueSelected.connect(
                        lambda text, scene_to_rename_=scene_to_rename: rename(self, scene_to_rename_, text))
                    self._input_dialog.setLabelText("Rename scene '" + scene_to_rename.human_readable_name + "' to:")
                    self._input_dialog.setWindowTitle("Rename Scene")
                    self._input_dialog.open()
                if isinstance(si.annotated_data, FilterGraphWidget):
                    page_to_rename = si.annotated_data
                    self._input_dialog = QInputDialog(self)
                    self._input_dialog.setInputMode(QInputDialog.TextInput)
                    self._input_dialog.textValueSelected.connect(
                        lambda text, page_to_rename_=page_to_rename: rename(self, page_to_rename_, text))
                    self._input_dialog.setLabelText("Rename filter page '" + page_to_rename.name + "' to:")
                    self._input_dialog.setWindowTitle("Rename Filter Page")
                    self._input_dialog.open()
                if isinstance(si.annotated_data, UIPage):
                    ui_page = si.annotated_data
                    self._input_dialog = QInputDialog(self)
                    self._input_dialog.setInputMode(QInputDialog.TextInput)
                    self._input_dialog.textValueSelected.connect(
                        lambda text, ui_page_=ui_page: rename(self, ui_page_, text))
                    self._input_dialog.setLabelText("Rename UI page '" + ui_page.title + "' to:")
                    self._input_dialog.setWindowTitle("Rename UI Page")
                    self._input_dialog.open()

    def _scene_item_double_clicked(self, item: AnnotatedTreeWidgetItem) -> None:
        data = item.annotated_data
        if isinstance(data, Scene):
            data = data.pages[0]
        self.switch_to_tab.emit(data)

    def _universe_item_double_clicked(self, item: AnnotatedTreeWidgetItem) -> None:
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        if isinstance(item.annotated_data, UsedFixture):
            current_widget = self._editor_tab_widget.currentWidget()
            if isinstance(current_widget, FilterPageTabWidget):
                for node in cast(Iterable[FixtureNode],
                                 cast(object, current_widget.node_editor.get_nodes_by_type("output.FixtureNode"))):
                    if node.fixture == item.annotated_data:
                        current_widget.node_editor.center_on([node])
                        return
                fix = current_widget.node_editor.create_node("output.FixtureNode",
                                                             name=item.annotated_data.name_on_stage)
                fix.setup(item.annotated_data)

    def _duplicate_scene(self, selected_items: list[QTreeWidgetItem]) -> None:
        i: int = 1
        for item in selected_items:
            if not isinstance(item, AnnotatedTreeWidgetItem):
                continue
            if not isinstance(item.annotated_data, Scene):
                continue
            sc = item.annotated_data.copy(item.annotated_data.board_configuration.scenes)
            sc.human_readable_name = f"Copy ({i}) of Scene '{sc.human_readable_name}'"
            self._show.broadcaster.scene_created.emit(sc)

    def _add_filter_page(self, selected_items: list[QTreeWidgetItem]) -> None:
        def add(c: ShowBrowserView, scene: Scene | FilterGraphWidget, text: str) -> None:
            if isinstance(scene, Scene):
                fp = FilterGraphWidget(scene)
                scene.insert_filter_graph_page(fp)
                fp.name = text
            # else:
            #    fp = FilterPage(scene.parent_scene)
            #    scene.child_pages.append(fp)
            #    fp.name = text
            c._refresh_scene_browser()

        for item in selected_items:
            if not isinstance(item, AnnotatedTreeWidgetItem):
                continue
            if isinstance(item.annotated_data, (FilterGraphWidget, Scene)):
                parent_to_append_to = item.annotated_data
                self._input_dialog = QInputDialog(self)
                self._input_dialog.setInputMode(QInputDialog.TextInput)
                self._input_dialog.textValueSelected.connect(
                    lambda text, parent=parent_to_append_to: add(self, parent, text))
                self._input_dialog.setLabelText("Please enter the name of the new page.")
                self._input_dialog.setWindowTitle("Enter Name")
                self._input_dialog.open()

    def _add_ui_page(self, selected_items: list[QTreeWidgetItem]) -> None:
        update_occurred = False
        for item in selected_items:
            if not isinstance(item, AnnotatedTreeWidgetItem):
                continue
            data = item.annotated_data
            if not isinstance(data, Scene):
                continue
            data.ui_pages.append(UIPage(data))
            update_occurred = True
        if update_occurred:
            self._refresh_scene_browser()
