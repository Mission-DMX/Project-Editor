from PySide6.QtWidgets import QVBoxLayout, QCheckBox, QWidget

from model import UIWidget, UIPage, Filter
from model.virtual_filters import PanTiltConstantFilter
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import \
    PanTiltConstantContentWidget


class PanTiltConstantControlUIWidget(UIWidget):

    def __init__(self, fid: str, parent: UIPage, filter_model: Filter | None, configuration: dict[str, str]):
        super().__init__(fid, parent, configuration)
        self._command_chain: list[tuple[str, str]] = [] # ??
        if not isinstance(filter_model, PanTiltConstantFilter):
            print("the filter has to be a PanTiltConstantFilter")
        self._filter = filter_model
        self._player_widget = None


    def generate_update_content(self) -> list[tuple[str, str]]:
        return self._command_chain

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget is None:
            # self._player_widget.deleteLater()
            self._player_widget = self.construct_widget(parent)
        return self._player_widget

    def construct_widget(self, parent: QWidget | None):
        w = QWidget(parent)
        layout = QVBoxLayout()

        pan_tilt = PanTiltConstantContentWidget(self._filter, w)
        layout.addWidget(pan_tilt)

        self._activated = QCheckBox()
        layout.addWidget(self._activated)

        w.setLayout(layout)
        return w


    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget is None: # Todo: Do these have to differ?
            self._player_widget = self.construct_widget(parent)
        return self._player_widget


    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = PanTiltConstantControlUIWidget(self.filter_id, self.parent, None, self.configuration)
        super().copy_base(w)
        return w


    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        return None
        # if self._dialog_widget:
        #     return self._dialog_widget
        # w = QListWidget(parent)
        # if self._config_cue_list_widget:
        #     for item_index in range(self._config_cue_list_widget.count()):
        #         template_item = self._config_cue_list_widget.item(item_index)
        #         item = AnnotatedListWidgetItem(w)
        #         item.setText(template_item.text())
        #         item.annotated_data = template_item
        #         w.addItem(item)
        # w.itemDoubleClicked.connect(self._config_item_double_clicked)
        # self._dialog_widget = w
        # return w

    def insert_action(self):
        command = ("value", self._filter.pan)
        self._command_chain.append(command)
        command = ("value", self._filter.tilt)
        self._command_chain.append(command)
        self.push_update()
        self._command_chain.clear()
