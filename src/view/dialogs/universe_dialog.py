# coding=utf-8
"""dialog for editing patching universe"""
from PySide6 import QtWidgets

import proto


class UniverseDialog(QtWidgets.QDialog):
    """dialog for editing patching universe"""

    def __init__(self, patching_universe_or_id: proto.UniverseControl_pb2.Universe | int,
                 parent: object = None) -> None:
        super().__init__(parent)
        if type(patching_universe_or_id) is int:
            patching_proto: proto.UniverseControl_pb2.Universe = proto.UniverseControl_pb2.Universe(
                id=patching_universe_or_id,
                remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                    ip_address="10.0.15.1",
                    port=6454,
                    universe_on_device=patching_universe_or_id
                )
            )
        else:
            patching_proto: proto.UniverseControl_pb2.Universe = patching_universe_or_id

        self.output: proto.UniverseControl_pb2.Universe = patching_proto
        self._widgets = QtWidgets.QStackedWidget(self)
        self._switch_button = QtWidgets.QPushButton("ftdi dongle")
        self._switch_button.clicked.connect(self._change_widget)

        ftdi_dongle = patching_proto.ftdi_dongle
        ftdi_items = [["vendor id", ftdi_dongle.vendor_id], ["product id", ftdi_dongle.product_id],
                      ["serial", ftdi_dongle.serial], ["device_name", ftdi_dongle.device_name]]
        remote_location = patching_proto.remote_location
        art_net_items: list[list[str, any]] = [["ip address", remote_location.ip_address],
                                               ["port", remote_location.port],
                                               ["universe on device", remote_location.universe_on_device]]

        ftdi_widget, self._ftdi_widgets = _generate_widget(ftdi_items, "ftdi dongle")
        art_net_widget, self._remote_location_widgets = _generate_widget(art_net_items, "art net")
        self._widgets.addWidget(art_net_widget)
        self._widgets.addWidget(ftdi_widget)

        layout_fixture = QtWidgets.QVBoxLayout()
        layout_fixture.addWidget(self._switch_button)
        layout_fixture.addWidget(self._widgets)

        layout_exit = QtWidgets.QHBoxLayout()
        self._ok = QtWidgets.QPushButton()
        self._ok.setText("Okay")
        self._cancel = QtWidgets.QPushButton()
        self._cancel.setText("cancel")
        layout_exit.addWidget(self._cancel)
        layout_exit.addWidget(self._ok)

        layout_fixture.addLayout(layout_exit)

        self.setLayout(layout_fixture)

        self._ok.clicked.connect(self.ok)
        self._cancel.clicked.connect(self.cancel)

    def _change_widget(self) -> None:
        if self._switch_button.text() == "ftdi dongle":
            self._switch_button.setText("art net")
            self._widgets.setCurrentIndex(1)
        else:
            self._switch_button.setText("ftdi dongle")
            self._widgets.setCurrentIndex(0)

    def ok(self) -> None:
        """accept the universe"""
        if self._widgets.currentIndex() == 0:
            # art net
            self.output = proto.UniverseControl_pb2.Universe(
                id=self.output.id,
                remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                    ip_address=self._remote_location_widgets[0].text(),
                    port=int(self._remote_location_widgets[1].text()),
                    universe_on_device=int(self._remote_location_widgets[2].text())
                )
            )
        else:
            # ftdi dongle
            self.output = proto.UniverseControl_pb2.Universe(
                id=self.output.id,
                ftdi_dongle=proto.UniverseControl_pb2.Universe.USBConfig(
                    vendor_id=int(self._ftdi_widgets[0].text()),
                    product_id=int(self._ftdi_widgets[1].text()),
                    serial=self._ftdi_widgets[2].text(),
                    device_name=self._ftdi_widgets[3].text()
                )
            )
        self.accept()

    def cancel(self) -> None:
        """cancel universe"""
        self.reject()


def _generate_widget(items: list[list[str, any]], name: str) -> tuple[QtWidgets.QWidget, list[QtWidgets.QLineEdit]]:
    output = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout()
    widgets = []
    for index, item in enumerate(items):
        label = QtWidgets.QLabel(item[0])
        widget = QtWidgets.QLineEdit(str(item[1]))
        widgets.append(widget)
        layout.addWidget(label, index, 0)
        layout.addWidget(widget, index, 1)

    complete_layout = QtWidgets.QVBoxLayout()
    complete_layout.addWidget(QtWidgets.QLabel(name))
    complete_layout.addLayout(layout)
    output.setLayout(complete_layout)
    return output, widgets
