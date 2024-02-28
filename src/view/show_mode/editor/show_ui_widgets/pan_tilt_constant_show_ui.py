from PySide6.QtWidgets import QVBoxLayout, QCheckBox, QWidget, QLabel, QComboBox

from controller.cli.joystick_handling import JoystickHandler
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
        self._filter.register_observer(self, self.insert_action)

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

        self._choosenJoystick = QComboBox()
        self._choosenJoystick.addItems(JoystickHandler.joystickMap.keys())
        self._choosenJoystick.currentTextChanged.connect(lambda x: self._filter.setjoystick(JoystickHandler.joystickMap[x]))
        layout.addWidget(self._choosenJoystick)

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
        # Todo: Do we need this?
        return QLabel()

    def insert_action(self):
        command = ("{}_16bit_pan:value".format(self._filter_id), str(int(self._filter.pan*65535)))
        self._command_chain.append(command)
        command = ("{}_16bit_tilt:value".format(self._filter_id), str(int(self._filter.tilt*65535))) # Todo: inverse Tilt?
        self._command_chain.append(command)
        self.push_update()
        self._command_chain.clear()
