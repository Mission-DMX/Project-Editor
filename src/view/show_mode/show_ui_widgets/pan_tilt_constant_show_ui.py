from logging import getLogger

from PySide6.QtWidgets import QComboBox, QDialog, QLabel, QVBoxLayout, QWidget

from controller.joystick.joystick_handling import JoystickHandler
from model import Filter, UIPage, UIWidget
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import (
    PanTiltConstantContentWidget,
)

logger = getLogger(__name__)


class PanTiltConstantControlUIWidget(UIWidget):

    def __init__(self, parent: UIPage, configuration: dict[str, str]) -> None:
        super().__init__(parent, configuration)
        self._command_chain: list[tuple[str, str]] = []  # ??
        self._filter = None
        self._player_widget: QWidget | None = None
        self._conf_widget: QWidget | None = None

    def set_filter(self, f: "Filter", i: int):
        if not f:
            return
        super().set_filter(f, i)
        self.associated_filters["pan_tilt_vfilter_fid"] = f.filter_id
        if not isinstance(f, PanTiltConstantFilter):
            logger.info("the filter has to be a PanTiltConstantFilter")
        self._filter = f
        self._filter.register_observer(self, self.insert_action)

    def generate_update_content(self) -> list[tuple[str, str]]:
        return self._command_chain

    def get_player_widget(self, parent: QWidget | None) -> QWidget:
        if self._player_widget is not None:
            self._player_widget.deleteLater()
        self._player_widget = self.construct_widget(parent)
        return self._player_widget

    def construct_widget(self, parent: QWidget | None):
        w = QWidget(parent)
        layout = QVBoxLayout()

        pan_tilt = PanTiltConstantContentWidget(self._filter, w)
        layout.addWidget(pan_tilt)

        self._chosen_joystick = QComboBox()
        self._chosen_joystick.addItems(JoystickHandler.joystickMap.keys())
        self._chosen_joystick.currentTextChanged.connect(
            lambda x: self._filter.set_joystick(JoystickHandler.joystickMap[x]))
        layout.addWidget(self._chosen_joystick)

        w.setLayout(layout)
        return w

    def get_configuration_widget(self, parent: QWidget | None) -> QWidget:
        if self._conf_widget is not None:
            self._conf_widget.deleteLater()
        self._conf_widget = self.construct_widget(parent)
        self._conf_widget.setEnabled(False)
        return self._conf_widget

    def copy(self, new_parent: "UIPage") -> "UIWidget":
        w = PanTiltConstantControlUIWidget(self.parent, self.configuration)
        w.set_filter(self._filter, 0)
        super().copy_base(w)
        return w

    def get_config_dialog_widget(self, parent: QDialog) -> QWidget:
        return QLabel()

    def insert_action(self) -> None:
        # TODO add support for separated constants
        combined_fid = self.associated_filters["pan_tilt_vfilter_fid"]
        command = (f"{combined_fid}_16bit_pan:value", str(int(self._filter.pan * 65535)))
        self._command_chain.append(command)
        command = (
            f"{combined_fid}_16bit_tilt:value", str(int(self._filter.tilt * 65535)))  # Todo: inverse Tilt?
        self._command_chain.append(command)
        self.push_update()
        self._command_chain.clear()
