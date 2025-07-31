from logging import getLogger

from PySide6.QtWidgets import (
    QColorDialog,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from model import BoardConfiguration, ColorHSI
from model.filter import FilterTypeEnumeration
from model.macro import Macro
from view.action_setup_view._command_insertion_dialog import _CommandInsertionDialog
from view.action_setup_view._command_insertion_dialog import escape_argument as esc
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import \
    PanTiltConstantContentWidget
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorLabel

logger = getLogger(__name__)


class ConstantUpdateInsertionDialog(_CommandInsertionDialog):
    def __init__(self, parent: QWidget, macro: Macro, show: BoardConfiguration, update_callable: callable) -> None:
        super().__init__(
            parent, macro,
            [
                FilterTypeEnumeration.VFILTER_POSITION_CONSTANT,
                FilterTypeEnumeration.FILTER_CONSTANT_8BIT,
                FilterTypeEnumeration.FILTER_CONSTANT_16_BIT,
                FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                FilterTypeEnumeration.FILTER_CONSTANT_COLOR,
            ],
            show, update_callable,
        )
        self._int_tb = QSpinBox()
        self._int_tb.setMinimum(0)
        self._int_tb.setEnabled(False)
        int_tb_layout = QVBoxLayout()
        int_tb_layout.addWidget(QLabel("Value:"))
        int_tb_layout.addWidget(self._int_tb)
        int_tb_layout.addStretch()
        int_panel = QWidget()
        int_panel.setLayout(int_tb_layout)
        self.custom_layout.addWidget(int_panel)

        self._float_tb = QDoubleSpinBox()
        self._float_tb.setEnabled(False)
        float_tb_layout = QVBoxLayout()
        float_tb_layout.addWidget(QLabel("Value:"))
        float_tb_layout.addWidget(self._float_tb)
        float_tb_layout.addStretch()
        float_panel = QWidget()
        float_panel.setLayout(float_tb_layout)
        self.custom_layout.addWidget(float_panel)

        self._pan_tilt_widget = PanTiltConstantContentWidget(None, enable_joystick=False)
        self._pan_tilt_widget.setEnabled(False)
        self.custom_layout.addWidget(self._pan_tilt_widget)

        self._color_panel = QWidget()
        self._color = ColorHSI(0, 0, 0)
        self._color_picker = QColorDialog()
        self._color_picker.accepted.connect(self._select_color)
        color_layout = QVBoxLayout()
        color_label_layout = QHBoxLayout()
        self._color_label = ColorLabel()
        self._color_label.setFixedWidth(16)
        self._color_label.setFixedHeight(16)
        color_label_layout.addWidget(QLabel("Current Color:"))
        color_label_layout.addSpacing(15)
        color_label_layout.addWidget(self._color_label)
        color_label_layout.addStretch()
        color_layout.addLayout(color_label_layout)
        select_color_button = QPushButton("Select Color")
        select_color_button.clicked.connect(self._color_picker.show)
        color_layout.addWidget(select_color_button)
        color_layout.addStretch()
        self._color_panel.setLayout(color_layout)
        self._color_panel.setEnabled(False)
        self.custom_layout.addWidget(self._color_panel)

    def get_command(self) -> str:
        if self._filter.filter_type in [FilterTypeEnumeration.FILTER_CONSTANT_8BIT, FilterTypeEnumeration.FILTER_CONSTANT_16_BIT]:
            return f"showctl filtermsg {self._scene.scene_id} {esc(self.filter_id)} value {self._int_tb.value()}"
        elif self._filter.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT:
            return f"showctl filtermsg {self._scene.scene_id} {esc(self.filter_id)} value {self._float_tb.value()}"
        elif self._filter.filter_type == FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            return (
                f"showctl filtermsg {self._scene.scene_id} {esc(self.filter_id)}_16bit_pan "
                f"value {int(self._pan_tilt_widget.pan * 65535)}\n"
                f"showctl filtermsg {self._scene.scene_id} {esc(self.filter_id)}_16bit_tilt "
                f"value {int(self._pan_tilt_widget.tilt * 65535)}"
            )
        else:
            qtc = self._color.to_qt_color()
            hexcode = f"rgb: {int(qtc.redF() * 255):02X}{int(qtc.greenF() * 255):02X}{int(qtc.blueF() * 255):02X}"
            return f"showctl filtermsg {self._scene.scene_id} {esc(self.filter_id)} value {esc(self._color.format_for_filter())} # {hexcode}"

    def on_filter_selected(self) -> None:
        if self._filter.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_8BIT:
            self._int_tb.setMaximum(255)
            self._int_tb.setEnabled(True)
            self.custom_layout.setCurrentIndex(0)
        elif self._filter.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_16_BIT:
            self._int_tb.setMaximum(65565)
            self._int_tb.setEnabled(True)
            self.custom_layout.setCurrentIndex(0)
        elif self._filter.filter_type == FilterTypeEnumeration.FILTER_CONSTANT_FLOAT:
            self._float_tb.setEnabled(True)
            self.custom_layout.setCurrentIndex(1)
        elif self._filter.filter_type == FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            self._pan_tilt_widget.setEnabled(True)
            self.custom_layout.setCurrentIndex(2)
        else:
            self._color_panel.setEnabled(True)
            self.custom_layout.setCurrentIndex(3)

    def _select_color(self) -> None:
        self._color = ColorHSI.from_qt_color(self._color_picker.selectedColor())
        self._color_label.set_color(self._color)
