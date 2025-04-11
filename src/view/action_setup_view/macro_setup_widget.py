from PySide6.QtWidgets import QLabel, QListWidget, QSplitter, QTextEdit, QToolBar, QVBoxLayout, QWidget

from model import Broadcaster


class MacroSetupWidget(QSplitter):

    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        self._broadcaster = Broadcaster()
        self._macro_panel: QWidget = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Macros"))
        self._macro_actions = QToolBar(self._macro_panel)
        self._macro_actions.addAction("New Macro")
        # TODO connect action
        self._macro_panel.setLayout(layout)
        layout.addWidget(self._macro_actions)
        self._macro_list = QListWidget(self._macro_panel)
        self._macro_list.itemSelectionChanged.connect(self._selected_macro_changed)
        layout.addWidget(self._macro_list)
        self.addWidget(self._macro_panel)
        self._trigger_panel = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Triggers"))
        self._trigger_actions = QToolBar(self._trigger_panel)
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
        self._content_panel_actions.addAction("Insert Cue Switch")
        # TODO connect action
        layout.addWidget(self._content_panel_actions)
        self._editor_area = QTextEdit(self._content_panel)
        self._editor_area.setAcceptRichText(False)
        layout.addWidget(self._editor_area)
        self._content_panel.setLayout(layout)
        self.addWidget(self._content_panel)
        self.setStretchFactor(2, 2)
        self._broadcaster.clear_board_configuration.connect(self.clear)
        self._broadcaster.macro_added_to_show_file.connect(self._macro_added)

    def _selected_macro_changed(self):
        pass
        # TODO implement repopulation of trigger list
        # TODO update content panel

    def clear(self):
        self._macro_list.clear()
        self._trigger_list.clear()
        self._editor_area.clear()

    def _macro_added(self, new_macros_id: int):
        pass  # TODO get macro from index and add it to the list
