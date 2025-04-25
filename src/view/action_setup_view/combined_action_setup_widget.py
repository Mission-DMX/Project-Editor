from typing import TYPE_CHECKING

from PySide6.QtWidgets import QTabWidget, QWidget

from model import Broadcaster
from view.action_setup_view.event_setup_widget import EventSetupWidget
from view.action_setup_view.macro_setup_widget import MacroSetupWidget

if TYPE_CHECKING:
    from model.board_configuration import BoardConfiguration


class CombinedActionSetupWidget(QTabWidget):

    """A tab view for setup of events and action."""

    def __init__(self, parent: QWidget | None, b: Broadcaster, show: "BoardConfiguration"):
        super().__init__(parent=parent)
        self._event_tab = EventSetupWidget(self, b)
        self.addTab(self._event_tab, "Events")
        self._macro_tab = MacroSetupWidget(self, show)
        self.addTab(self._macro_tab, "Macros")
