# coding=utf-8
"""Widget to create multiple scenes and manage filters.

Usage (where self is a QWidget and board_configuration is a BoardConfiguration):
    node_editor = NodeEditor(self, board_configuration)
    self.addWidget(node_editor)
"""
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QInputDialog, QSplitter, QTabBar, QTabWidget, QWidget

from controller.file.transmitting_to_fish import transmit_to_fish
from model.board_configuration import BoardConfiguration, Broadcaster, Scene
from model.scene import FilterPage
from view.show_mode.editor.editor_tab_widgets.scenetab import SceneTabWidget
from view.show_mode.editor.editor_tab_widgets.ui_widget_editor.scene_ui_page_editor_widget import \
    SceneUIPageEditorWidget

from .editing_utils import add_scene_to_show
from .editor_tab_widgets.bankset_tab import BankSetTabWidget
from .show_browser.show_browser import ShowBrowser


class ShowEditorWidget(QSplitter):
    """Node Editor to create and manage filters."""

    def __init__(self, board_configuration: BoardConfiguration, bcaster: Broadcaster, parent: QWidget) -> None:
        super().__init__(parent)
        self._broadcaster = bcaster
        self._board_configuration = board_configuration
        self._opened_pages = set()
        self._opened_banksets = set()
        self._opened_uieditors = set()

        # Buttons to add or remove scenes from show
        self._open_page_tab_widget = QTabWidget(self)
        self._open_page_tab_widget.setTabsClosable(True)
        self._open_page_tab_widget.addTab(QWidget(), "+")
        plus_button = self._open_page_tab_widget.tabBar().tabButton(
            self._open_page_tab_widget.count() - 1, QTabBar.ButtonPosition.RightSide
        )
        if plus_button:
            plus_button.resize(0, 0)

        self._open_page_tab_widget.tabBarClicked.connect(self._tab_bar_clicked)
        self._open_page_tab_widget.tabCloseRequested.connect(self._remove_tab)

        # Toolbar for io/network actions
        self._toolbar: list[QAction] = []
        # save_show_file_button = QAction("Save Show")
        # load_show_file_button = QAction("Load Show")

        # save_show_file_button.triggered.connect(lambda: show_save_showfile_dialog(self.parent(),
        #                                                                          self._board_configuration))
        # load_show_file_button.triggered.connect(lambda: show_load_showfile_dialog(self.parent(),
        #                                                                          self._board_configuration))

        # self._toolbar.append(save_show_file_button)
        # self._toolbar.append(load_show_file_button)

        self._show_browser = ShowBrowser(parent, board_configuration, self._open_page_tab_widget)

        self.addWidget(self._show_browser.widget)
        self.addWidget(self._open_page_tab_widget)

        board_configuration.broadcaster.scene_created.connect(self._add_scene_tab)
        board_configuration.broadcaster.scene_open_in_editor_requested.connect(self._add_scene_tab)
        board_configuration.broadcaster.bankset_open_in_editor_requested.connect(self._add_bankset_tab)
        board_configuration.broadcaster.uipage_opened_in_editor_requested.connect(self._add_uipage_tab)
        board_configuration.broadcaster.delete_scene.connect(self._remove_tab)

    def _select_scene_to_be_removed(self):
        scene_index, ok_button_pressed = QInputDialog.getInt(self, "Remove a scene", "Scene index (0-index)")
        if ok_button_pressed and 0 <= scene_index < self._open_page_tab_widget.tabBar().count() - 2:
            self._board_configuration.broadcaster.delete_scene()

    @property
    def toolbar(self) -> list[QAction]:
        """toolbar for node_mode"""
        return self._toolbar

    def _tab_bar_clicked(self, index: int):
        """Handles adding/deleting button action.
        
        Args:
            index: Index of the clicked tab
        """
        # Left to right, first "+" button, second "-" button
        if index == self._open_page_tab_widget.tabBar().count() - 1:
            self._add_button_clicked()

    def _add_button_clicked(self):
        add_scene_to_show(self, self._board_configuration)

    def _add_scene_tab(self, page: Scene | FilterPage) -> SceneTabWidget | None:
        """Creates a tab for a scene
        
        Args:
            page: The scene to be added
        """
        if isinstance(page, Scene):
            page = page.pages[0]

        if page in self._opened_pages:
            for tab_index in range(self._open_page_tab_widget.count()):
                tab = self._open_page_tab_widget.widget(tab_index)
                if isinstance(tab, SceneTabWidget):
                    if tab.scene == page:
                        self._open_page_tab_widget.setCurrentIndex(tab_index)
                        return tab
            return None

        # Each scene is represented by its own editor
        self._opened_pages.add(page)
        scene_tab = SceneTabWidget(page)
        # Move +/- buttons one to the right and insert new tab for the scene
        self._open_page_tab_widget.insertTab(self._open_page_tab_widget.tabBar().count() - 1, scene_tab,
                                             page.parent_scene.human_readable_name + "/" + page.name)
        # When loading scene from a file, set displayed tab to first loaded scene
        if (self._open_page_tab_widget.count() == 2 or
                self._board_configuration.default_active_scene == page.parent_scene.scene_id):
            self._open_page_tab_widget.setCurrentWidget(scene_tab)
        return scene_tab

    def _add_bankset_tab(self, data: dict):
        bankset = data["bankset"]
        if bankset in self._opened_banksets:
            for tab_index in range(self._open_page_tab_widget.count()):
                tab = self._open_page_tab_widget.widget(tab_index)
                if isinstance(tab, BankSetTabWidget):
                    if tab.bankset == bankset:
                        self._open_page_tab_widget.setCurrentIndex(tab_index)
                        return tab
            return None

        self._opened_banksets.add(bankset)
        tab = BankSetTabWidget(self._open_page_tab_widget, bankset)
        self._open_page_tab_widget.insertTab(
            self._open_page_tab_widget.tabBar().count() - 1,
            tab,
            bankset.description
        )
        self._open_page_tab_widget.setCurrentWidget(tab)

    def _add_uipage_tab(self, data: dict):
        uipage = data["uipage"]
        if uipage in self._opened_uieditors:
            for tab_index in range(self._open_page_tab_widget.count()):
                tab = self._open_page_tab_widget.widget(tab_index)
                if isinstance(tab, SceneUIPageEditorWidget):
                    if tab.ui_page == uipage:
                        self._open_page_tab_widget.setCurrentIndex(tab_index)
                        return tab
            return None

        self._opened_uieditors.add(uipage)
        tab = SceneUIPageEditorWidget(uipage, self._open_page_tab_widget)
        self._open_page_tab_widget.insertTab(
            self._open_page_tab_widget.tabBar().count() - 1,
            tab,
            uipage.scene.human_readable_name + "/UI Page"  # TODO query index
        )
        self._open_page_tab_widget.setCurrentWidget(tab)

    def _remove_tab(self, scene_or_index: Scene | int):
        """Removes the tab corresponding to the scene or index.

        Args:
            scene_or_index: The that is being removed.
        """
        if isinstance(scene_or_index, Scene):
            for index in range(self._open_page_tab_widget.count() - 1):
                tab_widget = self._open_page_tab_widget.widget(index)
                if not isinstance(tab_widget, SceneTabWidget):
                    continue
                if tab_widget.scene == scene_or_index:
                    widget_index = self._open_page_tab_widget.indexOf(tab_widget)
                    if self._open_page_tab_widget.count() > 0:
                        self._open_page_tab_widget.setCurrentIndex(widget_index - 1)
                    self._open_page_tab_widget.removeTab(widget_index)
                    self._opened_pages.remove(tab_widget.filter_page)
                    return
        else:
            widget = self._open_page_tab_widget.widget(scene_or_index)
            if isinstance(widget, SceneTabWidget):
                self._opened_pages.remove(widget.filter_page)
            elif isinstance(widget, BankSetTabWidget):
                self._opened_banksets.remove(widget.bankset)
            elif isinstance(widget, SceneUIPageEditorWidget):
                self._opened_uieditors.remove(widget.ui_page)
            self._open_page_tab_widget.removeTab(scene_or_index)

    def _send_show_file(self) -> None:
        """Send the current board configuration as a xml file to fish"""
        transmit_to_fish(self._board_configuration)
