# coding=utf-8
"""Patching Mode"""
import random

from PySide6 import QtWidgets, QtGui

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
        items = [
            ([1, 4, 5, 8, 10, 13, 15, 18],
             [False, False, False, False, False, False, False, False],
             UsedFixture(name="Grundlicht", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["SL1", "Streu", "SL2", "Sammel", "Sammel", "SL3", "Streu", "SL4"])
                         )
             ),
            ([20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
             [True, True, False, True, True, True, True, True, True, True, True, True, True],
             UsedFixture(name="MH1", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Pan", "Tilt", "Dimm", "Strob", "Rot", "Grün", "Blau", "Weiß", "Zoom",
                                             "Linse", "auto Farb", "auto Zoom", "auto beweg"])
                         )
             ),
            ([40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52],
             [True, True, False, True, True, True, True, True, True, True, True, True, True],
             UsedFixture(name="MH2", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Pan", "Tilt", "Dimm", "Strob", "Rot", "Grün", "Blau", "Weiß", "Zoom",
                                             "Linse", "auto Farb", "auto Zoom", "auto beweg"])
                         )
             ),
            ([60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72],
             [True, True, False, True, True, True, True, True, True, True, True, True, True],
             UsedFixture(name="MH3", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Pan", "Tilt", "Dimm", "Strob", "Rot", "Grün", "Blau", "Weiß", "Zoom",
                                             "Linse", "auto Farb", "auto Zoom", "auto beweg"])
                         )
             ),
            ([80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92],
             [True, True, False, True, True, True, True, True, True, True, True, True, True],
             UsedFixture(name="MH4", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Pan", "Tilt", "Dimm", "Strob", "Rot", "Grün", "Blau", "Weiß", "Zoom",
                                             "Linse", "auto Farb", "auto Zoom", "auto beweg"])
                         )
             ),
            ([125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141],
             [True, True, True, True, True, False, True, True, True, True, True, True, True, True, True, True, True],
             UsedFixture(name="Spot", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Pan", "Pan Fein", "Tilt", "Tilt Fein", "geschwindigkeit", "Dim",
                                             "Strob 255-an", "Farbrad", "Gobo1", "Gobo2", "Gobo3", "Fokus", "Zoom",
                                             "Prisma", "Prisma Rotation", "auto Show 255-Musik", "auto move 255-Musik"])
                         )
             ),
            ([150, 151, 152, 153, 154, 155, 156, 157],
             [False, True, True, True, True, True, True, True],
             UsedFixture(name="LED Gang", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Dim", "Rot", "Grün", "Blau", "Strob", "255-Musik", "",
                                             "einschalt verzögerung"])
                         )
             ),
            ([160, 161, 162, 163, 164, 165, 166, 167, 168, 169],
             [True, True, True, True, True, True, True, True, True, False],
             UsedFixture(name="LED Front", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Rot", "Grün", "Blau", "Weiß", "Amber", "UV", "Farb Macro", "Strobe",
                                             "Betriebsart 255-Musik", "Dim"])
                         )
             ),
            ([170, 171, 172, 173, 174, 175, 176, 177],
             [False, True, True, True, True, True, True, True],
             UsedFixture(name="LED Stage1", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Dim", "Rot", "Grün", "Blau", "Strob", "255-Musik", "",
                                             "einschalt verzögerung"])
                         )
             ),
            ([180, 181, 182, 183, 184, 185, 186, 187],
             [False, True, True, True, True, True, True, True],
             UsedFixture(name="LED Stage2", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Dim", "Rot", "Grün", "Blau", "Strob", "255-Musik", "",
                                             "einschalt verzögerung"])
                         )
             ),
            ([190, 191, 192, 193, 194, 195, 196, 197],
             [False, True, True, True, True, True, True, True],
             UsedFixture(name="LED Stage3", short_name="", categories=set(), comment="",
                         mode=Mode(name="", shortName="",
                                   channels=["Dim", "Rot", "Grün", "Blau", "Strob", "255-Musik", "",
                                             "einschalt verzögerung"])
                         )
             )

        ]
        for item in items:
            channel = item[0]
            ignore_black = item[1]
            fixture = item[2]
            color = "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
            for count, index in enumerate(channel):
                # for index in range(len(fixture.mode['channels'])):
                item = self._broadcaster.patching_universes[0].patching[index - 1]
                item.fixture = fixture
                item.fixture_channel = count
                item.color = color
                item.ignore_black = ignore_black[count]
