"""simple non-blocking Yes No Dialog"""

from collections.abc import Callable

from PySide6.QtWidgets import QDialog, QFormLayout, QLabel, QMessageBox, QPushButton, QStyle, QWidget

_ICON_MAP: dict[QMessageBox.Icon, QStyle.StandardPixmap] = {
    QMessageBox.Icon.Information: QStyle.StandardPixmap.SP_MessageBoxInformation,
    QMessageBox.Icon.Warning: QStyle.StandardPixmap.SP_MessageBoxWarning,
    QMessageBox.Icon.Critical: QStyle.StandardPixmap.SP_MessageBoxCritical,
    QMessageBox.Icon.Question: QStyle.StandardPixmap.SP_MessageBoxQuestion,
}


class YesNoDialog(QDialog):
    """simple non-blocking Yes No Dialog"""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        question: str,
        success_action: Callable[[], None],
        icon: QMessageBox.Icon = QMessageBox.Icon.Question,
        default_accept: bool = True,
    ) -> None:
        super().__init__(parent)
        self._layout = QFormLayout()
        self.setWindowTitle(title)
        pixmap = self.style().standardIcon(_ICON_MAP[icon]).pixmap(32, 32)
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        self._layout.addRow(icon_label, QLabel(question))

        self._yes_button = QPushButton("Yes")
        self._yes_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton))
        self._yes_button.clicked.connect(self._yes__button_pressed)

        self._no_button = QPushButton("No")
        self._no_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton))
        self._no_button.clicked.connect(self._no_button_pressed)
        if not default_accept:
            self._yes_button.setDefault(False)
            self._yes_button.setAutoDefault(False)

            self._no_button.setDefault(True)
            self._no_button.setAutoDefault(True)
            self._no_button.setFocus()

        self._layout.addRow(self._yes_button, self._no_button)

        self.setLayout(self._layout)
        self._success_action = success_action
        self.open()

    def _yes__button_pressed(self) -> None:
        self.close()
        self._success_action()

    def _no_button_pressed(self) -> None:
        self.close()
