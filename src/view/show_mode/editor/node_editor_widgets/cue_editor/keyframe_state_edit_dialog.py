from collections.abc import Callable

from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QPushButton,
    QSpinBox,
    QWidget,
)

from model import ColorHSI
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import (
    KeyFrame,
    State,
    StateColor,
    StateDouble,
    StateEightBit,
    StateSixteenBit,
)


class KeyFrameStateEditDialog(QDialog):
    def __init__(self, parent: QWidget, kf: KeyFrame, s: State, repaint_function: Callable):
        super().__init__(parent=parent)
        self._layout = QFormLayout()

        if isinstance(s, StateEightBit):
            self._input = QSpinBox()
            self._input.setSingleStep(1)
            self._input.setMinimum(0)
            self._input.setMaximum(255)
            self._input.setValue(s._value)
            self._layout.addRow("Value:", self._input)
        elif isinstance(s, StateSixteenBit):
            self._input = QSpinBox()
            self._input.setSingleStep(1)
            self._input.setMinimum(0)
            self._input.setMaximum(65535)
            self._input.setValue(s._value)
            self._layout.addRow("Value:", self._input)
        elif isinstance(s, StateDouble):
            self._input = QDoubleSpinBox()
            self._input.setSingleStep(0.1)
            self._input.setValue(s._value)
            self._input.setMinimum(-1000000)
            self._layout.addRow("Value:", self._input)
        elif isinstance(s, StateColor):
            self._input = QColorDialog(self)
            r, g, b = s.color.to_rgb()
            self._input.setCurrentColor(QColor.fromRgb(r, g, b))
            dialog_open_push_button = QPushButton("Choose color")
            dialog_open_push_button.clicked.connect(self.choose_color_clicked)
            self._layout.addRow("", dialog_open_push_button)

        self._transition_select = QComboBox()
        self._transition_select.addItems(["edg", "lin", "sig", "e_i", "e_o"])
        self._transition_select.setCurrentText(s.transition)
        self._transition_select.setEditable(False)
        self._layout.addRow("", self._transition_select)

        self._ok_button = QPushButton("Update")
        self._ok_button.pressed.connect(self._ok_pressed)
        self._layout.addRow("", self._ok_button)

        self._delete_kf_button = QPushButton("Delete Keyframe")
        self._delete_kf_button.setIcon(QIcon.fromTheme("edit-delete"))
        self._delete_kf_button.pressed.connect(self._delete_pressed)
        self._layout.addRow("Danger!", self._delete_kf_button)
        self.setLayout(self._layout)
        self._keyframe = kf
        self._state = s
        self._repaint_function = repaint_function

    def _ok_pressed(self) -> None:
        if isinstance(self._input, (QSpinBox, QDoubleSpinBox)):
            self._state._value = self._input.value()
        else:
            c = self._input.currentColor().toHsl()
            h = float(c.hue())
            s = c.saturationF()
            i = c.lightnessF()
            self._state.color = ColorHSI(h, s, i)
        self._state.transition = self._transition_select.currentText()
        self._repaint_function()
        self.close()

    def _delete_pressed(self) -> None:
        self._keyframe.delete_from_parent_cue()
        self.close()
        self._repaint_function()

    def choose_color_clicked(self):
        self._input.open()
