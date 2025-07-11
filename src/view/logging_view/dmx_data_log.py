# coding=utf-8
"""Widget for displaying DMX current data"""

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QTimer

import proto.DirectMode_pb2
from model import Broadcaster, Universe
from model.final_globals import FinalGlobals


# TODO komplett
class DmxDataLogWidget(QtWidgets.QWidget):
    """Widget to Log DMX Data"""

    def __init__(self, broadcaster: Broadcaster):
        super().__init__()
        self.setGeometry(self.geometry().x(), self.geometry().y(), 150, FinalGlobals.get_screen_height())
        self._broadcaster = broadcaster
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._request_dmx_data)

        self._widgets = QtWidgets.QTabWidget(self)
        self._universes: list[tuple[Universe, list[DmxLogItem]]] = []

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._widgets)
        self.setLayout(layout)

        self._broadcaster.add_universe.connect(self.react_add_universe)
        self._broadcaster.dmx_from_fish.connect(self.react_dmx_data)
        self.setMinimumWidth(350)

    def showEvent(self, event):
        """show logging Window start timer"""

        self._request_dmx_data()
        self._timer.start()

    def closeEvent(self, event):
        """close logging Window stp timer"""
        self._timer.stop()

    def _request_dmx_data(self):
        """send signal to request dmx data from fish for each universe"""
        for universe in self._universes:
            self._broadcaster.send_request_dmx_data.emit(universe[0])

    def react_add_universe(self, universe: Universe):
        """react on add universe Signal"""
        universe_items = []
        tab = QtWidgets.QTabWidget(self._widgets)
        tab_layout = QtWidgets.QVBoxLayout(tab)
        scroll = QtWidgets.QScrollArea(tab)

        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_widget = QtWidgets.QWidget(scroll)
        layout = QtWidgets.QVBoxLayout(scroll_widget)
        #        for i in range(0, 512):
        #            item = DmxLogItem(patching_universe.patching[i])
        #            universe.append(item)
        #            layout.addWidget(item)
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        self._widgets.addTab(tab, str(len(self._universes)))
        self._universes.append((universe, universe_items))

    def react_dmx_data(self, dmx: proto.DirectMode_pb2.dmx_output):
        """react on dmx data signal from fish"""
        for index, item in enumerate(dmx.channel_data[1:]):
            self._universes[dmx.universe_id - 1][1][index].update_value(str(item))


class DmxLogItem(QtWidgets.QWidget):
    """log Item for DMX signal"""

    def __init__(self, channel, parent=None):
        super().__init__(parent)
        element_size = 35
        self.setFixedSize(int(element_size * 9.5), element_size)

        address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.address + 1), self)
        address_label.setFixedSize(element_size, element_size)
        address_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        address_label.setMargin(0)

        self._value_label: QtWidgets.QLabel = QtWidgets.QLabel("250", self)
        self._value_label.setFixedSize(element_size, element_size)
        self._value_label.setMargin(0)

        # fixture_label: QtWidgets.QLabel = QtWidgets.QLabel(channel.fixture.name, self)
        # channel.updated_fixture.connect(lambda: fixture_label.setText(channel.fixture.name))
        # fixture_label.setFixedSize(element_size * 7, element_size)
        # fixture_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # fixture_label.setMargin(0)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(address_label)
        layout.addWidget(self._value_label)
        # layout.addWidget(fixture_label)
        self.setLayout(layout)

    def update_value(self, value: str):
        """update Value label"""
        self._value_label.setText(value)
