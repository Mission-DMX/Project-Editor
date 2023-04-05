from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from DMXModel import Universe
from Network import NetworkManager
from Style import Style
from widgets.DirectEditor.DirectEditorWidget import DirectEditorWidget
from widgets.PatchPlan.patch_plan_widget import PatchPlanWidget


class UniverseSelector(QtWidgets.QTabWidget):
    def __init__(self, universes: list[Universe], fish_connector: NetworkManager, parent=None):
        super().__init__(parent=parent)
        self._fish_connector = fish_connector
        self.setStyleSheet(Style.WIDGET)
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        for universe in universes:
            self.add_universe(universe)

    def add_universe(self, universe: Universe) -> None:
        if self._fish_connector.already_started:
            self._fish_connector.generate_universe(universe)
            self._fish_connector.send_universe(universe)

        splitter = QtWidgets.QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        custom_editor: PatchPlanWidget = PatchPlanWidget(universe, parent=splitter)
        splitter.addWidget(custom_editor)

        direct_editor: DirectEditorWidget = DirectEditorWidget(universe, self._fish_connector, parent=splitter)
        splitter.addWidget(direct_editor)

        self.addTab(splitter, str(universe.address))
