from PySide6.QtWidgets import QTableWidget, QWidget


class MacroSetupWidget(QTableWidget):

    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        # TODO implement list of configured macros
        # TODO implement trigger configuration cell
        # TODO implement script writing cell using custom widget (displaying preview and edit button
        #  -> Text Area w/ command creation wizards)
