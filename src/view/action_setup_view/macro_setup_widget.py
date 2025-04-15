import os
from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QSplitter, QToolBar, QVBoxLayout, QWidget)

from model import Broadcaster
from model.macro import Macro, Trigger
from view.action_setup_view._cli_syntax_highlighter import CLISyntaxHighlighter
from view.action_setup_view.cue_switch_dialog import _InsertCueSwitchDialog
from view.action_setup_view.new_trigger_dialog import _NewTriggerDialog
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

if TYPE_CHECKING:
    from model.board_configuration import BoardConfiguration

logger = getLogger(__file__)


class _TriggerListItemWidget(QWidget):
    def __init__(self, parent: QWidget, text:str, t: Trigger):
        super().__init__(parent)
        self._trigger = t
        self._enabled_cb = QCheckBox(self)
        self._enabled_cb.setChecked(t.enabled)
        self._enabled_cb.setToolTip("Enabled")
        t.enabled_changed.connect(self._enabled_cb.setChecked)
        self._enabled_cb.checkStateChanged.connect(self._check_changed)
        self._label = QLabel(self)
        self._label.setText(text)
        layout = QHBoxLayout()
        layout.addWidget(self._enabled_cb)
        layout.addWidget(self._label)
        layout.addStretch()
        self.setLayout(layout)

    def _check_changed(self):
        new_state = self._enabled_cb.isChecked()
        if new_state != self._trigger.enabled:
            self._trigger.enabled = new_state


class MacroSetupWidget(QSplitter):

    def __init__(self, parent: QWidget | None, show_config: "BoardConfiguration"):
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._show: "BoardConfiguration" = show_config
        self._selected_macro: Macro | None = None
        self._macro_panel: QWidget = QWidget(self)
        self._dialog: QDialog | None = None
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Macros"))
        self._macro_actions = QToolBar(self._macro_panel)
        self._import_macro_action: QAction = QAction()
        self._import_macro_action.setIcon(QIcon.fromTheme("document-open"))
        self._import_macro_action.setText("Import")
        self._import_macro_action.triggered.connect(self._import_macro_clicked)
        self._macro_actions.addAction(self._import_macro_action)
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
        self._new_trigger_action = QAction()
        self._new_trigger_action.setText("New Trigger")
        self._new_trigger_action.triggered.connect(self._add_new_trigger_pressed)
        self._trigger_actions.addAction(self._new_trigger_action)
        layout.addWidget(self._trigger_actions)
        self._trigger_list = QListWidget(self._trigger_panel)
        layout.addWidget(self._trigger_list)
        self._trigger_panel.setLayout(layout)
        self._content_panel = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Contents"))
        self._content_panel_actions = QToolBar(self._content_panel)
        self._content_panel_actions.setEnabled(False)
        self._run_macro_action = QAction()
        self._run_macro_action.setText("Run Macro")
        self._run_macro_action.triggered.connect(self._run_macro_pressed)
        self._run_macro_action.setIcon(QIcon.fromTheme("system-run"))
        self._content_panel_actions.addAction(self._run_macro_action)
        self._export_macro_action = QAction()
        self._export_macro_action.setText("Export Macro")
        self._export_macro_action.setIcon(QIcon.fromTheme("document-save"))
        self._export_macro_action.triggered.connect(self._export_macro_clicked)
        self._content_panel_actions.addAction(self._export_macro_action)
        self._insert_cue_switch_action = QAction()
        self._insert_cue_switch_action.setText("Insert Cue Switch")
        self._insert_cue_switch_action.triggered.connect(self._insert_cue_switch_clicked)
        self._content_panel_actions.addAction(self._insert_cue_switch_action)
        self._insert_sequence_trigger_action = QAction()
        self._insert_sequence_trigger_action.setText("Insert Sequence Trigger")
        # TODO connect action
        self._insert_sequence_trigger_action.setEnabled(False)
        self._content_panel_actions.addAction(self._insert_sequence_trigger_action)
        self._insert_constant_update_action = QAction()
        self._insert_constant_update_action.setText("Insert Constant Update")
        self._insert_constant_update_action.setEnabled(False)
        # TODO connect action
        self._content_panel_actions.addAction(self._insert_constant_update_action)
        layout.addWidget(self._content_panel_actions)
        self._editor_area = QPlainTextEdit(self._content_panel)
        self._editor_area.setEnabled(False)
        self._editor_area.textChanged.connect(self._editor_area_text_changed)
        self._highlighter = CLISyntaxHighlighter(self._editor_area.document())
        layout.addWidget(self._editor_area)
        self._content_panel.setLayout(layout)
        self.addWidget(self._content_panel)
        self.setStretchFactor(2, 2)
        self._broadcaster.clear_board_configuration.connect(self.clear)
        self._broadcaster.macro_added_to_show_file.connect(self._macro_added)

    def _selected_macro_changed(self):
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
        if self._selected_macro is not None:
            self._trigger_actions.setEnabled(True)
            self._editor_area.setEnabled(True)
            self._content_panel_actions.setEnabled(True)
            for trigger in self._selected_macro.all_triggers:
                self._trigger_added(trigger)
            self._editor_area.document().setPlainText(self._selected_macro.content)
        else:
            self._trigger_actions.setEnabled(False)
            self._content_panel_actions.setEnabled(False)
            self._editor_area.setEnabled(False)
            self._editor_area.document().clear()

    def clear(self):
        self._macro_list.clear()
        self._trigger_list.clear()
        self._editor_area.clear()

    def _trigger_added(self, t: Trigger):
        item = AnnotatedListWidgetItem(self._trigger_list)
        item.annotated_data = t
        tw = _TriggerListItemWidget(
            self._trigger_list,
            f"[{str(self._trigger_list.count()) if t.enabled else '-'}] {t.name}",
            t
        )
        item.setSizeHint(tw.sizeHint())
        self._trigger_list.addItem(item)
        self._trigger_list.setItemWidget(item, tw)

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
        m = Macro(self._show)
        m.name = "New Macro"
        self._show.add_macro(m)

    def _add_new_trigger_pressed(self):
        if self._selected_macro is None:
            return
        self._dialog = _NewTriggerDialog(self, self._selected_macro)
        self._dialog.added_callable = self._trigger_added
        self._dialog.show()

    def _editor_area_text_changed(self):
        if self._selected_macro is not None:
            self._selected_macro.content = self._editor_area.toPlainText()

    def _run_macro_pressed(self):
        if self._selected_macro is None:
            return
        logger.info(f"Running macro {self._selected_macro.name} from manual trigger.")
        self._selected_macro.c.return_text = ""
        success = self._selected_macro.exec()
        text = self._selected_macro.c.return_text
        self._dialog = QMessageBox(self)
        self._dialog.setWindowTitle("Macro Output")
        self._dialog.setText(text.replace("\n", "<br />" if len(text) > 0 else "<i>No output was generated</i>"))
        self._dialog.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Critical)
        self._dialog.show()

    def _import_macro_clicked(self):
        self._create_file_dialog(True)
        self._dialog.accepted.connect(self._load_macro)
        self._dialog.show()

    def _create_file_dialog(self, open: bool):
        self._dialog = QFileDialog(self)
        self._dialog.setModal(True)
        self._dialog.setNameFilter("Macro (*.macro)")
        self._dialog.setViewMode(QFileDialog.ViewMode.Detail)
        if open:
            self._dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            self._dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        else:
            self._dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            self._dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        if self._show.file_path:
            self._dialog.setDirectory(os.path.dirname(os.path.realpath(self._show.file_path)))
        else:
            self._dialog.setDirectory(os.path.expanduser("~"))

    def _load_macro(self):
        if not isinstance(self._dialog, QFileDialog):
            logger.error(f"Expected the dialog to be of type QFileDialog. Got {type(self._dialog)} instead.")
        for f_path in self._dialog.selectedFiles():
            with open(f_path, "r") as f:
                m = Macro(self._show)
                m.name = os.path.splitext(os.path.basename(f_path))[0]
                m.content = f.read()
                self._show.add_macro(m)

    def _export_macro_clicked(self):
        self._create_file_dialog(False)
        self._dialog.accepted.connect(self._export_macro)
        self._dialog.show()

    def _export_macro(self):
        if not isinstance(self._dialog, QFileDialog):
            logger.error(f"Expected the dialog to be of type QFileDialog. Got {type(self._dialog)} instead.")
        file_name = self._dialog.selectedFiles()[0]
        if not os.path.splitext(file_name)[1] == ".macro":
            file_name += ".macro"
        with open(file_name, "w") as f:
            f.write(self._selected_macro.content)

    def _insert_cue_switch_clicked(self):
        if self._selected_macro is None:
            return
        self._dialog = _InsertCueSwitchDialog(self, self._selected_macro, self._show, self._macro_content_changed)
        self._dialog.show()

    def _macro_content_changed(self):
        if self._selected_macro is not None:
            self._editor_area.document().setPlainText(self._selected_macro.content)
