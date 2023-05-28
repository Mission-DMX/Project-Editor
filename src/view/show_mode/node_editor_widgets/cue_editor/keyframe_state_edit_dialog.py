from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QWidget, QFormLayout, QPushButton

from view.show_mode.node_editor_widgets.cue_editor.cue import KeyFrame, State


class KeyFrameStateEditDialog(QDialog):
    def __init__(self, parent: QWidget, kf: KeyFrame, s: State, repaint_function):
        super().__init__(parent=parent)
        self._layout = QFormLayout()

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

    def _ok_pressed(self):
        # TODO update state
        self._repaint_function()

    def _delete_pressed(self):
        self._keyframe.delete_from_parent_cue()
        self.close()
        self._repaint_function()
