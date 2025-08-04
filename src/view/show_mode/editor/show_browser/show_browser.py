
"""This file provides the ShowBrowser widget."""

import os.path
from functools import partial

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QInputDialog,
    QMenu,
    QMessageBox,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from controller.file.transmitting_to_fish import transmit_to_fish
from model import BoardConfiguration, Scene, UIPage
from model.control_desk import BankSet
from model.ofl.fixture import UsedFixture
from model.scene import FilterPage
from utility import resource_path
from view.show_mode.editor.editing_utils import add_scene_to_show
from view.show_mode.editor.editor_tab_widgets.scenetab import SceneTabWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog
from view.utility_widgets.universe_tree_browser_widget import UniverseTreeBrowserWidget

from .annotated_item import AnnotatedTreeWidgetItem
from .fixture_to_filter import place_fixture_filters_in_scene


class ShowBrowser:
    """This class provides a navigation bar / browser for the complete show."""

    _filter_icon = QIcon(resource_path(os.path.join("resources", "icons", "filter.svg")))
    _scene_browser_tab_icon = QIcon(resource_path(os.path.join("resources", "icons", "showbrowser-show.svg")))
    _universe_browser_tab_icon = QIcon(resource_path(os.path.join("resources", "icons", "showbrowser-universe.svg")))
    _filter_browser_tab_icon = QIcon(resource_path(os.path.join("resources", "icons", "showbrowser-filterpages.svg")))
    _fader_icon = QIcon(resource_path(os.path.join("resources", "icons", "faders.svg")))
    _uipage_icon = QIcon(resource_path(os.path.join("resources", "icons", "uipage.svg")))

    def __init__(self, parent: QWidget, show: BoardConfiguration, editor_tab_browser: QTabWidget) -> None:
        self._recently_created_scene = None
        self._widget = QWidget(parent)
        self._widget.setMaximumWidth(450)
        self._widget.setMinimumWidth(250)
        self._tab_widget = QTabWidget()
        self._scene_browsing_tree = QTreeWidget()
        self._universe_browsing_tree = UniverseTreeBrowserWidget()
        self._filter_browsing_tree = QTreeWidget()
        self._tab_widget.addTab(self._scene_browsing_tree, ShowBrowser._scene_browser_tab_icon, "Show")
        self._tab_widget.addTab(self._universe_browsing_tree, ShowBrowser._universe_browser_tab_icon, "Universes")
        self._tab_widget.addTab(self._filter_browsing_tree, ShowBrowser._filter_browser_tab_icon, "Current Scene")

        self._scene_browsing_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._scene_browsing_tree.customContextMenuRequested.connect(self._scene_context_menu_triggered)
        self._scene_browsing_tree.itemDoubleClicked.connect(self._scene_item_double_clicked)

        self._universe_browsing_tree.itemDoubleClicked.connect(self._universe_item_double_clicked)

        self._scene_browsing_tree.setColumnCount(2)
        self._filter_browsing_tree.setColumnCount(1)

        self._tool_bar = QToolBar()
        self._tool_bar.addAction(QIcon.fromTheme("list-add"), "Add Scene", lambda: self._add_element_pressed())
        self._tool_bar.addAction(QIcon.fromTheme("document-properties"), "Edit", lambda: self._edit_element_pressed())
        self._tool_bar.addAction(QIcon.fromTheme("view-refresh"), "Refresh", lambda: self._refresh_all())
        self._tool_bar.addAction(
            QIcon.fromTheme("document-send"), "Send showfile to fish", lambda: self._upload_showfile()
        )

        self._toolbar_edit_action = self._tool_bar.actions()[1]
        self._toolbar_edit_action.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self._tool_bar)
        layout.addWidget(self._tab_widget)
        self._widget.setLayout(layout)

        self._editor_tab_widget = editor_tab_browser
        self._show: BoardConfiguration | None = None
        self._selected_scene: Scene | None = None
        if show:
            self.board_configuration = show
        self._input_dialog = None
        self._show.broadcaster.show_file_loaded.connect(self._refresh_all)
        self._show.broadcaster.commit_button_pressed.connect(self._upload_showfile)
        self._show.broadcaster.scene_created.connect(self._add_scene_to_scene_browser)

    def _refresh_all(self) -> None:
        self._refresh_scene_browser()
        self._universe_browsing_tree.refresh()
        self._refresh_filter_browser()

    @property
    def widget(self) -> QWidget:
        return self._widget

    @property
    def board_configuration(self) -> BoardConfiguration | None:
        return self._show

    @board_configuration.setter
    def board_configuration(self, b: BoardConfiguration | None) -> None:
        self._show = b
        self._universe_browsing_tree._show = b
        self._refresh_all()
        self.selected_scene = None

    @property
    def selected_scene(self) -> Scene | None:
        return self._selected_scene

    @selected_scene.setter
    def selected_scene(self, s: Scene | None) -> None:
        self._selected_scene = s
        self._refresh_filter_browser()

    def _refresh_filter_browser(self) -> None:
        self._filter_browsing_tree.clear()

        def generate_tree_item(fp: FilterPage, parent: QTreeWidgetItem) -> QTreeWidgetItem:
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

    def _add_scene_to_scene_browser(self, s: Scene) -> None:
        if self._recently_created_scene == s:
            return
        self._recently_created_scene = s

        def add_filter_page(parent_item: AnnotatedTreeWidgetItem, fp: FilterPage) -> None:
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
        item.setExpanded(True)
        bankset_item = AnnotatedTreeWidgetItem(item)
        s.ensure_bankset()
        bankset_item.setText(0, "Bankset")
        bankset_item.setIcon(0, ShowBrowser._fader_icon)
        bankset_item.setText(1, s.linked_bankset.description)
        bankset_item.annotated_data = s.linked_bankset
        if len(s.ui_pages) < 1:
            s.ui_pages.append(UIPage(s))

        for i, ui_page in enumerate(s.ui_pages, start=1):
            uipage_item = AnnotatedTreeWidgetItem(item)
            uipage_item.setText(0, f"UI Page {i} '{ui_page.title}'")
            uipage_item.setIcon(0, ShowBrowser._uipage_icon)
            uipage_item.setText(1, f"{len(ui_page.widgets)} widgets")
            uipage_item.annotated_data = ui_page
        for fp in s.pages:
            add_filter_page(item, fp)
        self._scene_browsing_tree.insertTopLevelItem(self._scene_browsing_tree.topLevelItemCount(), item)

    def _refresh_scene_browser(self) -> None:
        self._recently_created_scene = None
        self._scene_browsing_tree.clear()
        if self._show:
            for scene in self._show.scenes:
                self._add_scene_to_scene_browser(scene)

    def _add_element_pressed(self) -> None:
        new_scene = add_scene_to_show(self._widget, self._show)
        if new_scene:
            self._add_scene_to_scene_browser(new_scene)

    def _edit_element_pressed(self) -> None:
        # TODO
        pass

    def _scene_context_menu_triggered(self, point: QPoint) -> None:
        selected_items = self._scene_browsing_tree.selectedItems()

        has_scenes = False
        has_filter_pages = False

        for si in selected_items:
            if isinstance(si, AnnotatedTreeWidgetItem):
                if isinstance(si.annotated_data, Scene):
                    has_scenes = True
                if isinstance(si.annotated_data, FilterPage):
                    has_filter_pages = True
                if isinstance(si.annotated_data, UIPage):
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

    def _delete_scenes_from_context_menu(self, items: list[AnnotatedTreeWidgetItem]) -> None:
        self._input_dialog = YesNoDialog(
            self.widget,
            "Are you sure?",
            f"Do you really want to delete the scene {', '.join([f"'{item.text(1)}'" for item in items])}",
            partial(self._delete_scenes_from_context_menu_accepted, items),
            QMessageBox.Icon.Warning,
            False,
        )

    def _delete_scenes_from_context_menu_accepted(self, items: list[AnnotatedTreeWidgetItem]) -> None:
        if self._input_dialog:
            self._input_dialog.close()
            self._input_dialog = None
        for si in items:
            if isinstance(si, AnnotatedTreeWidgetItem) and isinstance(si.annotated_data, Scene):
                scene_to_delete = si.annotated_data
                self._show.broadcaster.delete_scene.emit(scene_to_delete)
                del si
        self._refresh_scene_browser()

    def _rename_scene_from_context_menu(self, items: list[AnnotatedTreeWidgetItem]) -> None:
        def rename(c: ShowBrowser, scene: Scene | FilterPage, text: str) -> None:
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
                    self._input_dialog = QInputDialog(self.widget)
                    self._input_dialog.setInputMode(QInputDialog.TextInput)
                    self._input_dialog.textValueSelected.connect(
                        lambda text, scene_to_rename_=scene_to_rename: rename(self, scene_to_rename_, text)
                    )
                    self._input_dialog.setLabelText("Rename scene '" + scene_to_rename.human_readable_name + "' to:")
                    self._input_dialog.setWindowTitle("Rename Scene")
                    self._input_dialog.open()
                if isinstance(si.annotated_data, FilterPage):
                    page_to_rename = si.annotated_data
                    self._input_dialog = QInputDialog(self.widget)
                    self._input_dialog.setInputMode(QInputDialog.TextInput)
                    self._input_dialog.textValueSelected.connect(
                        lambda text, page_to_rename_=page_to_rename: rename(self, page_to_rename_, text)
                    )
                    self._input_dialog.setLabelText("Rename filter page '" + page_to_rename.name + "' to:")
                    self._input_dialog.setWindowTitle("Rename Filter Page")
                    self._input_dialog.open()
                if isinstance(si.annotated_data, UIPage):
                    ui_page = si.annotated_data
                    self._input_dialog = QInputDialog(self.widget)
                    self._input_dialog.setInputMode(QInputDialog.TextInput)
                    self._input_dialog.textValueSelected.connect(
                        lambda text, ui_page_=ui_page: rename(self, ui_page_, text)
                    )
                    self._input_dialog.setLabelText("Rename UI page '" + ui_page.title + "' to:")
                    self._input_dialog.setWindowTitle("Rename UI Page")
                    self._input_dialog.open()

    def _scene_item_double_clicked(self, item: AnnotatedTreeWidgetItem) -> None:
        if isinstance(item, AnnotatedTreeWidgetItem):
            data = item.annotated_data
            if isinstance(data, Scene):
                self._show.broadcaster.scene_open_in_editor_requested.emit(data.pages[0])
                if self._selected_scene != data:
                    self._selected_scene = data
                    self._refresh_filter_browser()
            elif isinstance(data, FilterPage):
                # TODO exchange for correct loading of page
                self._show.broadcaster.scene_open_in_editor_requested.emit(data)
                if self._selected_scene != data.parent_scene:
                    self._selected_scene = data.parent_scene
                    self._refresh_filter_browser()
            elif isinstance(data, BankSet):
                self._show.broadcaster.bankset_open_in_editor_requested.emit({"bankset": data})
            elif isinstance(data, UIPage):
                self._show.broadcaster.uipage_opened_in_editor_requested.emit({"uipage": data})

    def _universe_item_double_clicked(self, item: QTreeWidgetItem) -> None:
        if not isinstance(item, AnnotatedTreeWidgetItem):
            return
        if isinstance(item.annotated_data, UsedFixture):
            current_widget = self._editor_tab_widget.currentWidget()
            if isinstance(current_widget, SceneTabWidget) and place_fixture_filters_in_scene(
                item.annotated_data, current_widget.filter_page
            ):
                current_widget.refresh()

    def _upload_showfile(self) -> None:
        transmit_to_fish(self._show, False)

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
        def add(c: ShowBrowser, scene: Scene | FilterPage, text: str) -> None:
            if isinstance(scene, Scene):
                fp = FilterPage(scene)
                scene.insert_filterpage(fp)
                fp.name = text
            else:
                fp = FilterPage(scene.parent_scene)
                scene.child_pages.append(fp)
                fp.name = text
            c._refresh_scene_browser()

        for item in selected_items:
            if not isinstance(item, AnnotatedTreeWidgetItem):
                continue
            if isinstance(item.annotated_data, (FilterPage, Scene)):
                parent_to_append_to = item.annotated_data
                self._input_dialog = QInputDialog(self.widget)
                self._input_dialog.setInputMode(QInputDialog.TextInput)
                self._input_dialog.textValueSelected.connect(
                    lambda text, parent=parent_to_append_to: add(self, parent, text)
                )
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
