from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from controller.ofl.fixture import UsedFixture


class EffectCompilationWidget(QWidget):

    _background_css = """
    background-image: repeating-linear-gradient(
        90deg,
        #505050,
        #151515 1px
    ), repeating-linear-gradient(
      0deg,
      #303030,
      #101010 1px
    );
    background-blend-mode: screen;
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.setMinimumWidth(600)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: gray;")

    def add_fixture_or_group(self, fg: UsedFixture):
        # TODO implement
        pass
