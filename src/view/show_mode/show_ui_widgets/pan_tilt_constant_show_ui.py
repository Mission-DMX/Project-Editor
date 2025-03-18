# coding=utf-8
from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget

from controller.joystick.joystick_handling import JoystickHandler
from model import Filter, UIPage, UIWidget
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import \
    PanTiltConstantContentWidget


class PanTiltConstantControlUIWidget(UIWidget):

    def __init__(self, parent: UIPage, configuration: dict[str, str]):
        super().__init__(parent, configuration)
        self._command_chain: list[tuple[str, str]] = []  # ??
        self._filter = None
        self._player_widget = None

    def set_filter(self, f: "Filter", i: int):
        if not f:
            return
        self.associated_filters["pan_tilt_vfilter_fid"] = f.filter_id
        if not isinstance(f, PanTiltConstantFilter):
            print("the filter has to be a PanTiltConstantFilter")
        self._filter = f
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
        self._choosenJoystick.currentTextChanged.connect(
            lambda x: self._filter.set_joystick(JoystickHandler.joystickMap[x]))
        layout.addWidget(self._choosenJoystick)

        w.setLayout(layout)
        return w

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget is None:  # Todo: Do these have to differ?
            self._player_widget = self.construct_widget(parent)
        return self._player_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = PanTiltConstantControlUIWidget(self.parent, self.configuration)
        w.set_filter(self._filter, 0)
        super().copy_base(w)
        return w

    def get_config_dialog_widget(self, parent: QWidget) -> QWidget:
        return QLabel()

    def insert_action(self):
        # TODO add support for separated constants
        combined_fid = self.associated_filters["pan_tilt_vfilter_fid"]
        command = ("{}_16bit_pan:value".format(combined_fid), str(int(self._filter.pan * 65535)))
        self._command_chain.append(command)
        command = (
            "{}_16bit_tilt:value".format(combined_fid), str(int(self._filter.tilt * 65535)))  # Todo: inverse Tilt?
        self._command_chain.append(command)
        self.push_update()
        self._command_chain.clear()
