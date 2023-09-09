# coding=utf-8
"""Patching Mode"""
import random

from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QMessageBox

from model.broadcaster import Broadcaster
from model.patching_universe import PatchingUniverse
from ofl.fixture import UsedFixture, Mode
from view.patch_mode.patch_plan.patch_plan_selector import PatchPlanSelector
from view.patch_mode.patching.patching_select import PatchingSelect


class PatchMode(QtWidgets.QStackedWidget):
    """Patching Mode"""

    def __init__(self, parent):
        super().__init__(parent)
        self.addWidget(PatchPlanSelector(self))
        self.addWidget(PatchingSelect(self))
        self._broadcaster = Broadcaster()
        self._broadcaster.add_universe.connect(self._add_universe)
        self._broadcaster.connection_state_updated.connect(self._connection_changed)
        self._broadcaster.view_to_patch_menu.connect(lambda: self.setCurrentIndex(0))
        self._broadcaster.view_patching.connect(lambda: self.setCurrentIndex(1))
        self._broadcaster.view_leave_patching.connect(lambda: self.setCurrentIndex(0))

        self._toolbar: list[QtGui.QAction] = []
        #        save_button = QtGui.QAction("Save")
        load_button = QtGui.QAction("Load")
        #        save_button.triggered.connect(self._save_patching)
        load_button.triggered.connect(self._load_patching)

        #        self._toolbar.append(save_button)
        self._toolbar.append(load_button)

    @property
    def toolbar(self) -> list[QtGui.QAction]:
        """toolbar for Console mode"""
        return self._toolbar

    def _add_universe(self, universe: PatchingUniverse):
        self._broadcaster.patching_universes.append(universe)
        self._broadcaster.send_universe.emit(universe)

    def _connection_changed(self, connected):
        """connection to fish is changed"""
        if connected:
            for universe in self._broadcaster.patching_universes:
                self._broadcaster.send_universe.emit(universe)

    def _save_patching(self):
        msgbox = QMessageBox()
        msgbox.setText("Diese Funktion sollte nicht mehr verwendet werden. Sie wird bald entfernt.")
        msgbox.open()
        data: str = ""
        for universe in self._broadcaster.patching_universes:
            for channel in universe.patching:
                data += ""
                for channel in universe.channels:
                    data += str(channel.value) + ","
                data = data[:-1]
                data += ";"
            data = data[:-1]
            data += "\n"
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "save Scene", "",
                                                             "Text Files (*.txt);;All Files (*)", )
        if file_name:
            with open(file_name, "w", encoding='UTF-8') as file:
                file.write(data)

    #        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "save Scene", "",
    #                                                             "Json Files (*.json);;All Files (*)", )
    #        if file_name:
    #            with open(file_name, "w", encoding='UTF-8') as file:
    #                file.write(
    #                    json.dumps(jsonpickle.encode(self._broadcaster.patching_universes, unpicklable=False), indent=4))

    #    def _load_patching(self):
    #        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "load Scene", "",
    #                                                             "Json Files (*.json);;All Files (*)", )
    #        if file_name:
    #            with open(file_name, "r", encoding='UTF-8') as file:
    #                data=json.loads(jsonpickle.decode(file.read()))
    #                for universe in data:
    #                    print(universe["_universe_proto"])
    #                    PatchingUniverse(universe["_universe_proto"])
    ##                    for channel in universe:

    # self._broadcaster.patching_universes=json.loads(jsonpickle.decode(file.read()))

    # print(self._broadcaster.patching_universes[0].universe_proto)
    # print(json.loads(jsonpickle.decode(file.read())))
    def _load_patching(self):
        msgbox = QMessageBox()
        msgbox.setText("Diese Funktion wurde entfernt. Die Patchdaten werden demnächst in der Showfile mitgespeichert"
                       "werden")
        msgbox.open()
        pass
