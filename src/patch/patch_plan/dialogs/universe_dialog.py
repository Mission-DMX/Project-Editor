"""Dialog for editing patching universe."""

from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget

import proto.UniverseControl_pb2


class UniverseDialog(QtWidgets.QDialog):
    """Dialog for editing patching universe."""

    def __init__(
        self, patching_universe_or_id: proto.UniverseControl_pb2.Universe | int, parent: QWidget = None
    ) -> None:
        """Dialog for editing patching universe."""
        super().__init__(parent)
        self.output = None

        self._widgets = QtWidgets.QStackedWidget(self)
        self._switch_button = QtWidgets.QPushButton("ftdi dongle")
        self._switch_button.clicked.connect(self._change_widget)

        ftdi_items: list[str] = ["vendor id", "product id", "serial", "device_name"]

        art_net_items: list[str] = ["ip address", "port", "universe on device"]

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
        self.setModal(True)

        if isinstance(patching_universe_or_id, int):
            self._id = patching_universe_or_id
            self._set_to_default(False)
            self._set_to_default()
        else:
            self._id = patching_universe_or_id.id
            self.patching_universe = patching_universe_or_id
            self._load_from_universe()

    def _set_to_default(self, remote_location: bool = True) -> None:
        if remote_location:
            self._remote_location_widgets[0].setText("10.0.15.1")
            self._remote_location_widgets[1].setText("6454")
            self._remote_location_widgets[2].setText(str(self._id))
        else:
            self._ftdi_widgets[0].setText("0403")
            self._ftdi_widgets[1].setText("6001")
            self._ftdi_widgets[2].setText("")
            self._ftdi_widgets[3].setText("")

    def _load_from_universe(self) -> None:
        if self.patching_universe.remote_location.ip_address:
            self._remote_location_widgets[0].setText(self.patching_universe.remote_location.ip_address)
            self._remote_location_widgets[1].setText(str(self.patching_universe.remote_location.port))
            self._remote_location_widgets[2].setText(str(self.patching_universe.remote_location.universe_on_device))
        else:
            self._ftdi_widgets[0].setText(str(self.patching_universe.ftdi_dongle.vendor_id))
            self._ftdi_widgets[1].setText(str(self.patching_universe.ftdi_dongle.product_id))
            self._ftdi_widgets[2].setText(self.patching_universe.ftdi_dongle.serial)
            self._ftdi_widgets[3].setText(self.patching_universe.ftdi_dongle.device_name)
            self._widgets.setCurrentIndex(1)

    def _change_widget(self) -> None:
        if self._switch_button.text() == "ftdi dongle":
            self._switch_button.setText("art net")
            self._widgets.setCurrentIndex(1)
        else:
            self._switch_button.setText("ftdi dongle")
            self._widgets.setCurrentIndex(0)

    def ok(self) -> None:
        """Handle Ok button."""
        if self._widgets.currentIndex() == 0:
            # art net
            self.output = proto.UniverseControl_pb2.Universe(
                id=self._id,
                remote_location=proto.UniverseControl_pb2.Universe.ArtNet(
                    ip_address=self._remote_location_widgets[0].text(),
                    port=int(self._remote_location_widgets[1].text()),
                    universe_on_device=int(self._remote_location_widgets[2].text()),
                ),
            )
        else:
            # ftdi dongle
            self.output = proto.UniverseControl_pb2.Universe(
                id=self._id,
                ftdi_dongle=proto.UniverseControl_pb2.Universe.USBConfig(
                    vendor_id=int(self._ftdi_widgets[0].text()),
                    product_id=int(self._ftdi_widgets[1].text()),
                    serial=self._ftdi_widgets[2].text(),
                    device_name=self._ftdi_widgets[3].text(),
                ),
            )
        self.accept()

    def cancel(self) -> None:
        """Handle cancel button."""
        self.reject()


def _generate_widget(items: list[str], name: str) -> tuple[QtWidgets.QWidget, list[QtWidgets.QLineEdit]]:
    """Generate a widget for a patching universe."""
    output = QtWidgets.QWidget()
    layout = QtWidgets.QGridLayout()
    widgets = []
    for index, item in enumerate(items):
        label = QtWidgets.QLabel(item)
        widget = QtWidgets.QLineEdit()
        widgets.append(widget)
        layout.addWidget(label, index, 0)
        layout.addWidget(widget, index, 1)

    complete_layout = QtWidgets.QVBoxLayout()
    complete_layout.addWidget(QtWidgets.QLabel(name))
    complete_layout.addLayout(layout)
    output.setLayout(complete_layout)
    return output, widgets
