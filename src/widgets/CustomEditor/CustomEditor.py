from PySide6 import QtWidgets

from src.DMXModel import Universe
from src.widgets.CustomEditor.TabWidget import CustomEditorTabWidget


class CustomEditorWidget(QtWidgets.QTabWidget):
    """Widget to add and edit specific channels. Individual channels can be named.

    Contains one (default) or more CustomEditorTabWidgets to control specific channels.

    Tabs can be added and removed dynamically.
    """

    def __init__(self, universes: list[Universe], parent=None):
        super().__init__(parent=parent)

        self._universes = universes
        self.setMinimumHeight(100)

        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        self.addTab(CustomEditorTabWidget(universes), str(1))

        self.addTab(QtWidgets.QWidget(), "+")
        self.addTab(QtWidgets.QWidget(), "-")

        self.tabBarClicked.connect(self._tab_bar)

    def _tab_bar(self, index: int) -> None:
        """Add or deletes an tab if the corresponding button was pressed."""
        if index == self.tabBar().count() - 2:
            text, ok = QtWidgets.QInputDialog.getText(self, "Add Custom Tab", "Tab Name")

            # TODO Create new tab and rearrange tab bar

        elif index == self.tabBar().count() - 1:
            text, ok = QtWidgets.QInputDialog.getText(self, "Remove Custom Tab", "Tab Name")

            # TODO Remove tab and rearrange tab bar