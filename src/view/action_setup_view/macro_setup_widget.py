from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QListWidget, QSplitter, QTextEdit, QToolBar, QVBoxLayout, QWidget

from model import Broadcaster
from model.macro import Macro
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from model.board_configuration import BoardConfiguration

logger = getLogger(__file__)


class MacroSetupWidget(QSplitter):

    def __init__(self, parent: QWidget | None, show_config: "BoardConfiguration"):
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._show: "BoardConfiguration" = show_config
        self._selected_macro: Macro | None = None
        self._macro_panel: QWidget = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Macros"))
        self._macro_actions = QToolBar(self._macro_panel)
        self.add_macro_action = QAction()
        self.add_macro_action.setText("New Macro")
        self.add_macro_action.triggered.connect(self._add_macro_pressed)
        self._macro_actions.addAction(self.add_macro_action)
        self._macro_panel.setLayout(layout)
        layout.addWidget(self._macro_actions)
        self._macro_list = QListWidget(self._macro_panel)
        self._macro_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._macro_list.itemSelectionChanged.connect(self._selected_macro_changed)
        # TODO add action to rename macro on double click
        layout.addWidget(self._macro_list)
        self.addWidget(self._macro_panel)
        self._trigger_panel = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Triggers"))
        self._trigger_actions = QToolBar(self._trigger_panel)
        self._trigger_actions.setEnabled(False)
        self._trigger_actions.addAction("New Trigger")
        # TODO connect action
        layout.addWidget(self._trigger_actions)
        self._trigger_list = QListWidget(self._trigger_panel)
        layout.addWidget(self._trigger_list)
        self._trigger_panel.setLayout(layout)
        self._content_panel = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Contents"))
        self._content_panel_actions = QToolBar(self._content_panel)
        self._content_panel_actions.setEnabled(False)
        self._content_panel_actions.addAction("Insert Cue Switch")
        # TODO connect action
        layout.addWidget(self._content_panel_actions)
        self._editor_area = QTextEdit(self._content_panel)
        self._editor_area.setAcceptRichText(False)
        self._editor_area.setEnabled(False)
        layout.addWidget(self._editor_area)
        self._content_panel.setLayout(layout)
        self.addWidget(self._content_panel)
        self.setStretchFactor(2, 2)
        self._broadcaster.clear_board_configuration.connect(self.clear)
        self._broadcaster.macro_added_to_show_file.connect(self._macro_added)

    def _selected_macro_changed(self):
        if self._selected_macro is not None:
            self._selected_macro.content = self._editor_area.toPlainText()
        selected_items = self._macro_list.selectedItems()
        if len(selected_items) < 1:
            self._selected_macro = None
        else:
            if not isinstance(selected_items[0], AnnotatedListWidgetItem):
                logger.error(f"Expected AnnotatedListWidgetItem with macro. Got {selected_items[0]} instead.")
            if len(selected_items) > 1:
                logger.warning(f"Expected only one selected macro. Got {len(selected_items)} instead. Using the first.")
            self._selected_macro = selected_items[0].annotated_data
        self._trigger_list.clear()
        i = 0
        if self._selected_macro is not None:
            self._trigger_actions.setEnabled(True)
            self._editor_area.setEnabled(True)
            self._content_panel_actions.setEnabled(True)
            for trigger in self._selected_macro.all_triggers:
                item = AnnotatedListWidgetItem(self._trigger_list)
                item.annotated_data = trigger
                item.setText(str(i))  # TODO replace with something more reasonable, based on condition
                self._trigger_list.addItem(item)
            self._editor_area.setText(self._selected_macro.content)
        else:
            self._trigger_actions.setEnabled(False)
            self._content_panel_actions.setEnabled(False)
            self._editor_area.setEnabled(False)
            self._editor_area.setText("")

    def clear(self):
        self._macro_list.clear()
        self._trigger_list.clear()
        self._editor_area.clear()

    def _macro_added(self, new_macros_id: int):
        m = self._show.get_macro(new_macros_id)
        if m is None:
            logger.error(f"Did not expect the newly created macro with index {new_macros_id} to not exist.")
        item = AnnotatedListWidgetItem(self._macro_list)
        item.annotated_data = m
        item.setText(f"[{new_macros_id}]: {m.name}")
        self._macro_list.addItem(item)
        if self._macro_list.count() == 1:
            self._macro_list.setCurrentIndex(self._macro_list.model().index(0, 0))

    def _add_macro_pressed(self):
        m = Macro()
        m.name = "New Macro"
        self._show.add_macro(m)
        pass  # TODO
