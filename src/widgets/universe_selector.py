from PySide6 import QtWidgets
from PySide6.QtCore import Qt

from Network import NetworkManager
from Style import Style
from DMXModel import Universe
from widgets.DirectEditor.DirectEditorWidget import DirectEditorWidget
from widgets.PatchPlan.patch_plan_widget import PatchPlanWidget


class UniverseSelector(QtWidgets.QTabWidget):
    def __init__(self, universes: list[Universe], fish_connector: NetworkManager, parent=None):
        super().__init__(parent=parent)
        self.parent = parent

        for universe in universes:
            splitter = QtWidgets.QSplitter(self)
            splitter.setOrientation(Qt.Vertical)

            self.setStyleSheet(Style.WIDGET)
            self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

            custom_editor: PatchPlanWidget = PatchPlanWidget(universe, parent=splitter)
            splitter.addWidget(custom_editor)

            direct_editor: DirectEditorWidget = DirectEditorWidget(universe, fish_connector, parent=splitter)
            splitter.addWidget(direct_editor)

            self.addTab(splitter, str(universe.address))
