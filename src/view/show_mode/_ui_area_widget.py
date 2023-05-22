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
        self._pages = []
        for up in ui.pages:
            container = QWidget()
            for wc in up.widgets:
                widget = wc.get_qt_widget()
                widget.setParent(container)
                widget.move(wc.position[0], wc.position[1])
                widget.setFixedSize(wc.size[0], wc.size[1])
            self._pages.append(container)
        if len(self._pages) > 0:
            self.setWidget(self._pages[0])

    def open_page(self, index: int):
        """This method loads the referenced ui page.

        Arguments:
            index -- The index of the page to load
        """
        pass
