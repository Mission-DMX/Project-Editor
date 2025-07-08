from logging import getLogger
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from controller.joystick.joystick_enum import JoystickList
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import (
    PanTiltConstantContentWidget,
)

if TYPE_CHECKING:
    from view.show_mode.editor.nodes import FilterNode

logger = getLogger(__name__)


class PanTiltConstantWidget(NodeEditorFilterConfigWidget):

    def __init__(self, filter_: PanTiltConstantFilter, parent: QWidget = None):
        super().__init__()
        self._filter = filter_
        self._parent_widget = QWidget(parent=parent)
        top_layout = QVBoxLayout()

        graph = PanTiltConstantContentWidget(self._filter, self._parent_widget)
        top_layout.addWidget(graph)
        self.cB8Bit = QCheckBox(self._parent_widget)
        self.cB16Bit = QCheckBox(self._parent_widget)
        self.cB8Bit.setText("8 Bit available")
        self.cB16Bit.setText("16 Bit available")
        self.cB8Bit.setChecked(self._filter.eight_bit_available)
        self.cB16Bit.setChecked(self._filter.sixteen_bit_available)
        top_layout.addWidget(self.cB8Bit)
        top_layout.addWidget(self.cB16Bit)
        self._parent_widget.setLayout(top_layout)

    def _get_configuration(self) -> dict[str, str]:
        return self._filter.filter_configurations

    def _load_configuration(self, conf: dict[str, str]):
        for key, value in conf.items():
            try:
                if key == "outputs":
                    self._filter.filter_configurations["outputs"] = value
                else:
                    logger.error(f"Unknown configuration key: {key}")

                    return False
            except:
                logger.info("error parsing configuration, value: %s for param: %s", value, key)
                return False
        return True

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        for key, value in parameters.items():
            try:
                if key == "pan":
                    self._filter.pan = float(value)
                elif key == "tilt":
                    self._filter.tilt = float(value)
                else:
                    logger.info("wrong key: %s", key)
                    return False
            except:
                logger.info("error parsing parameter, value: %s for param: %s", value, key)
                return False
        return True

    def _get_parameters(self) -> dict[str, str]:
        return {"pan": self._filter.pan,
                "tilt": self._filter.tilt}

    def parent_closed(self, filter_node: "FilterNode"):
        if self._filter.joystick == JoystickList.EVERY_JOYSTICK:
            self._filter.joystick = JoystickList.NO_JOYSTICK
        filter_node.outputs_changed(self.cB8Bit.isChecked(), self.cB16Bit.isChecked())

    def parent_opened(self):
        if self._filter.joystick == JoystickList.NO_JOYSTICK:
            self._filter.joystick = JoystickList.EVERY_JOYSTICK
        self.cB8Bit.setChecked(self._filter.eight_bit_available)
        self.cB16Bit.setChecked(self._filter.sixteen_bit_available)
