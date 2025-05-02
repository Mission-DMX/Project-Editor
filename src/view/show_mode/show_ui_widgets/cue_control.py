# coding=utf-8
from logging import getLogger

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFormLayout, QInputDialog, QLabel, QListWidget, QSpinBox, QToolBar, QVBoxLayout, QWidget

from model import Filter, UIPage, UIWidget
from model.file_support.cue_state import CueState
from model.virtual_filters.cue_vfilter import CueFilter
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue_filter_model import CueFilterModel
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem

logger = getLogger(__file__)


class CueControlUIWidget(UIWidget):

    def __init__(self, parent: UIPage, configuration: dict[str, str] | None = None):
        super().__init__(parent, configuration)
        self._statuslabel = QLabel()
        self._cues: list[tuple[str, int]] = []
        self._command_chain: list[tuple[str, str]] = []

        self._filter = None
        self._cue_state = CueState(self._filter)

        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self.update_time_passed)
        self._timer.start()

        self._player_cue_list_widget: QListWidget | None = None
        self._config_cue_list_widget: QListWidget | None = None
        self._player_widget: QWidget | None = None
        self._config_widget: QWidget | None = None
        self._input_dialog: QInputDialog | None = None
        self._dialog_widget: QWidget | None = None
        self._model: CueFilterModel | None = None

    def set_filter(self, f: "Filter", i: int):
        if not f:
            return
        if isinstance(self._filter, CueFilter):
            self._filter.linked_ui_widgets.remove(self)
        if self._filter is not None:
            f.scene.board_configuration.remove_filter_update_callback(
                self._filter.scene.scene_id, self._filter.filter_id, self._cue_state.update
            )
        super().set_filter(f, i)
        self.associated_filters["cue_filter"] = f.filter_id
        self._filter = f
        if isinstance(self._filter, CueFilter):
            self._filter.linked_ui_widgets.append(self)
        f.scene.board_configuration.register_filter_update_callback(
            f.scene.scene_id, f.filter_id, self._cue_state.update)
        self.update_model(clear_model=False)
        self._migrate_name_list()
        self._model = None

    def _migrate_name_list(self):
        cuelist_str = self.configuration.get("cue_names")
        if cuelist_str:
            logger.info("Migrating old cue name model")
            for entry_text in cuelist_str.split(";"):
                name, id = entry_text.split(":")
                id = int(id)
                cue = self._model.cues[id]
                if len(cue.name) == 0 or cue.name == "":
                    logger.info("Updating cue name %s to %s.", cue.name, name)
                    cue.name = name
            if isinstance(self._filter, Filter):
                logger.info("Saving cue model.")
                self.configuration.pop("cue_names")
                self._filter.filter_configurations.update(self._model.get_as_configuration())
                self.update_model()

    def update_model(self, clear_model: bool = True):
        self._cues.clear()
        if self._filter:
            self._model = CueFilterModel()
            self._model.load_from_configuration(self._filter.filter_configurations)
            self._cues.clear()
            for c in self._model.cues:
                cf = (c.name, len(self._cues))
                self._cues.append(cf)
        self._repopulate_lists()
        if clear_model:
            self._model = None

    def _repopulate_lists(self):
        for cue_list in [self._player_cue_list_widget, self._config_cue_list_widget]:
            if cue_list is None:
                continue
            cue_list.clear()
            for cue in self._cues:
                item = AnnotatedListWidgetItem(cue_list)
                item.setText(cue[0] if cue[0] else "No Name")
                item.annotated_data = cue
                cue_list.addItem(item)

    def generate_update_content(self) -> list[tuple[str, str]]:
        return self._command_chain

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget:
            self._player_widget.deleteLater()
        self._player_widget = self.construct_widget(parent, True)
        return self._player_widget

    def construct_widget(self, parent: QWidget | None, enabled: bool):
        w = QWidget(parent)
        layout = QVBoxLayout()
        toolbar = QToolBar(w)
        # TODO add Icons from theme
        toolbar.addAction("Play", lambda: self.insert_action("run_mode", "play"))
        toolbar.addAction("Pause", lambda: self.insert_action("run_mode", "pause"))
        toolbar.addAction("Play Cue", lambda: self.insert_action("run_mode", "to_next_cue"))
        toolbar.addAction("stop", lambda: self.insert_action("run_mode", "stop"))
        toolbar.addSeparator()
        toolbar.addAction("Run Cue", lambda: self.insert_action("run_cue", self.get_selected_cue_id()))
        toolbar.addAction("Load Cue", lambda: self.insert_action("next_cue", self.get_selected_cue_id()))
        toolbar.setEnabled(enabled)
        toolbar.setMinimumWidth(330)
        toolbar.setMinimumHeight(30)
        layout.addWidget(toolbar)
        cue_list = QListWidget(w)
        cue_list.setEnabled(enabled)
        cue_list.setMinimumHeight(300)
        if enabled:
            self._player_cue_list_widget = cue_list
        else:
            self._config_cue_list_widget = cue_list
        layout.addWidget(cue_list)
        self._repopulate_lists()
        self._statuslabel.setParent(w)
        self._statuslabel.setEnabled(enabled)
        self._statuslabel.setMinimumHeight(20)
        self._statuslabel.setVisible(True)
        self._statuslabel.setText("Init text")
        self._statuslabel.show()
        layout.addWidget(self._statuslabel)

        self.update_time_passed()

        w.setLayout(layout)
        w.setFixedHeight(int(self.configuration.get("widget_height") or "350"))
        return w

    def insert_action(self, action: str | None, state: str | None):
        if not action or not state:
            return
        command = (action, state)
        self._command_chain.append(command)
        self.push_update()
        self._command_chain.clear()

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if not self._config_widget:
            self._config_widget = self.construct_widget(parent, False)
        return self._config_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = CueControlUIWidget(new_parent, self.configuration)
        super().copy_base(w)
        w.set_filter(self._filter, 0)
        return w

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        if self._dialog_widget:
            return self._dialog_widget
        w = QWidget(parent)
        layout = QFormLayout()
        height_widget = QSpinBox(w)
        height_widget.setMinimum(350)
        height_widget.setValue(int(self.configuration.get("widget_height") or "350"))
        height_widget.valueChanged.connect(self._config_item_update_height)
        height_widget.setEnabled(True)
        layout.addRow("Height: ", height_widget)
        w.setLayout(layout)
        self._dialog_widget = w
        return w

    def _config_item_update_height(self, new_height: int):
        new_height = max(350, new_height)
        if self._config_widget is not None:
            self._config_widget.setFixedHeight(new_height)
        if self._player_widget is not None:
            self._player_widget.setFixedHeight(new_height)
        self.configuration["widget_height"] = str(new_height)

    def get_selected_cue_id(self) -> str | None:
        if self._player_cue_list_widget:
            for selected_cue_item in self._player_cue_list_widget.selectedItems():
                if isinstance(selected_cue_item, AnnotatedListWidgetItem):
                    return str(selected_cue_item.annotated_data[1])
        return None

    def update_time_passed(self):
        self._statuslabel.setText(str(self._cue_state))
