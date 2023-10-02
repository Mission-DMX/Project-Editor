from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QListWidget, QInputDialog

from model import UIWidget, UIPage, Filter
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem


class CueControlUIWidget(UIWidget):

    def __init__(self, fid: str, parent: UIPage, filter_model: Filter | None, configuration: dict[str, str]):
        super().__init__(fid, parent, configuration)
        self._cues: list[tuple[str, int]] = []
        self._command_chain: list[tuple[str, str]] = []

        cuelist_str = super().configuration.get("cue_names")
        if cuelist_str:
            for entry_text in cuelist_str.split(";"):
                name, id = entry_text.split(":")
                id = int(id)
                new_item = (name, id)
                self._cues.append(new_item)

        if filter_model:
            cuelist_str = filter_model.initial_parameters.get("cuelist")
            if cuelist_str:
                cuelist_count = cuelist_str.count("$") + 1
                while len(self._cues) < cuelist_count:
                    cf = ("", len(self._cues))
                    self._cues.append(cf)
                while len(self._cues) > cuelist_count:
                    self._cues.pop(-1)
        self._player_cue_list_widget: QListWidget | None = None
        self._config_cue_list_widget: QListWidget | None = None
        self._player_widget: QWidget | None = None
        self._config_widget: QWidget | None = None
        self._input_dialog: QInputDialog | None = None
        self._dialog_widget: QWidget | None = None

    @property
    def configuration(self) -> dict[str, str]:
        return {"cue_names": ";".join(["{}:{}".format(cue[0], cue[1]) for cue in self._cues])}

    def generate_update_content(self) -> list[tuple[str, str]]:
        return self._command_chain

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if not self._player_widget:
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
        for cue in self._cues:
            item = AnnotatedListWidgetItem(cue_list)
            item.setText(cue[0] if cue[0] else "No Name")
            item.annotated_data = cue
            cue_list.addItem(item)
        cue_list.setEnabled(enabled)
        cue_list.setMinimumHeight(100)
        if enabled:
            self._player_cue_list_widget = cue_list
        else:
            self._config_cue_list_widget = cue_list
        layout.addWidget(cue_list)
        w.setLayout(layout)
        return w

    def insert_action(self, action: str | None, state: str | None):
        if not action or not state:
            return
        command = (action, state)
        self._command_chain.append(command)
        self.push_update()

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if not self._config_widget:
            self._config_widget = self.construct_widget(parent, False)
        return self._config_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = CueControlUIWidget(self.filter_id, self.parent, None, self.configuration)
        super().copy_base(w)
        return w

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        if self._dialog_widget:
            return self._dialog_widget
        w = QListWidget(parent)
        if self._config_cue_list_widget:
            for item_index in range(self._config_cue_list_widget.count()):
                template_item = self._config_cue_list_widget.item(item_index)
                item = AnnotatedListWidgetItem(w)
                item.setText(template_item.text())
                item.annotated_data = template_item
                w.addItem(item)
        w.itemDoubleClicked.connect(self._config_item_double_clicked)
        self._dialog_widget = w
        return w

    def _config_item_double_clicked(self, item):
        if not isinstance(item, AnnotatedListWidgetItem):
            return
        self._input_dialog = QInputDialog(self._dialog_widget)
        self._input_dialog.setWindowTitle("Enter new cue name")
        self._input_dialog.setLabelText("Set name of cue {}:".format(item.annotated_data.annotated_data[1]))
        self._input_dialog.setTextValue("")
        self._input_dialog.accepted.connect(lambda: self._set_name(item, self._input_dialog.textValue()))
        self._input_dialog.open()

    def _set_name(self, item: AnnotatedListWidgetItem, new_name: str):
        item.setText(new_name)
        item.annotated_data.setText(new_name)
        original_cue = item.annotated_data.annotated_data
        new_cue = (new_name, original_cue[1])
        item.annotated_data.annotated_data = new_cue
        for i in range(len(self._cues)):
            if self._cues[i] == original_cue:
                self._cues[i] = new_cue

    def get_selected_cue_id(self) -> str | None:
        if self._player_cue_list_widget:
            for selected_cue_item in self._player_cue_list_widget.selectedItems():
                if isinstance(selected_cue_item, AnnotatedListWidgetItem):
                    return str(selected_cue_item.annotated_data[1])
        return None

