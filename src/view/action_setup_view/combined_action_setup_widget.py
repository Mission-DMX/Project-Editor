from PySide6.QtWidgets import QTabWidget, QWidget

from view.action_setup_view.event_setup_widget import EventSetupWidget
from view.action_setup_view.macro_setup_widget import MacroSetupWidget


class CombinedActionSetupWidget(QTabWidget):

    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        self._event_tab = EventSetupWidget(self)
        self.addTab(self._event_tab, "Events")
        self._macro_tab = MacroSetupWidget(self)
        self.addTab(self._macro_tab, "Macros")
