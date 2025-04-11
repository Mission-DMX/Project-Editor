from PySide6.QtWidgets import QLabel, QListWidget, QSplitter, QToolBar, QVBoxLayout, QWidget


class MacroSetupWidget(QSplitter):

    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        self._macro_panel: QWidget = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Macros"))
        self._macro_actions = QToolBar(self._macro_panel)
        self._macro_actions.addAction("New Macro")
        self._macro_panel.setLayout(layout)
        layout.addWidget(self._macro_actions)
        self._macro_list = QListWidget(self._macro_panel)
        self._macro_list.itemSelectionChanged.connect(self._selected_macro_changed)
        # TODO populate list of configured macros
        layout.addWidget(self._macro_list)
        self.addWidget(self._macro_panel)
        self._trigger_panel = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Triggers"))
        self._trigger_actions = QToolBar(self._trigger_panel)
        self._trigger_actions.addAction("New Trigger")
        layout.addWidget(self._trigger_actions)
        self._trigger_list = QListWidget(self._trigger_panel)
        layout.addWidget(self._trigger_list)
        self._trigger_panel.setLayout(layout)
        self._content_panel = QWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Contents"))
        self._content_panel_actions = QToolBar(self._content_panel)
        self._content_panel_actions.addAction("Insert Cue Switch")
        layout.addWidget(self._content_panel_actions)
        self._content_panel.setLayout(layout)
        self.addWidget(self._content_panel)
        # TODO implement script writing cell using custom widget (displaying preview and edit button
        #  -> Text Area w/ command creation wizards)
        # TODO set reasonable splitter ratios

    def _selected_macro_changed(self):
        pass
        # TODO implement repopulation of trigger list
        # TODO update content panel
