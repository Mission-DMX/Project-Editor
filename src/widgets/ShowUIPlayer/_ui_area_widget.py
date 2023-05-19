from PySide6.QtWidgets import QScrollArea, QWidget

from model.ui_configuration import ShowUI


class UIAreaWidget(QScrollArea):
    """This class displays the actual UI pages"""
    def __init__(self, ui: ShowUI, parent: QWidget = None):
        """Construct the UI page area

        Attributes:
            ui -- The structure containing the pages to be displayed
            parent -- The parent container of this widget
        """
        super().__init__(parent=parent)
        self._ui = ui

    def open_page(self, index: int):
        """This method loads the referenced ui page.

        Arguments:
            index -- The index of the page to load
        """
        pass
