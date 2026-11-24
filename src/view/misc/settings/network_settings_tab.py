"""Contains settings tab to use network settings specific to show files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from controller.utils.network_setting_application import apply_network_settings_and_notify

if TYPE_CHECKING:
    from model import BoardConfiguration


_AUTOMATIC_IP = "AUTOMATIC"


def _detect_ethernet_interfaces() -> list[str]:
    """Return the physical ethernet interface names present on the system.

    Filters out loopback, wireless, and virtual devices. Returns an empty list
    on non-Linux systems or when ``/sys/class/net`` is not readable.
    """
    net_dir = Path("/sys/class/net")
    if not net_dir.is_dir():
        return []
    interfaces: list[str] = []
    for entry in sorted(net_dir.iterdir()):
        try:
            if (entry / "type").read_text().strip() != "1":  # ARPHRD_ETHER
                continue
        except OSError:
            continue
        if not (entry / "device").exists():
            continue  # virtual bridge, veth, tun, ...
        if (entry / "wireless").is_dir() or (entry / "phy80211").exists():
            continue
        interfaces.append(entry.name)
    return interfaces


class _StringListWidget(QWidget):
    """List of strings with add/remove buttons.

    If ``unique_value`` is set, that specific value may appear at most once.
    """

    def __init__(self, parent: QWidget | None = None, placeholder: str = "",
                 unique_value: str | None = None) -> None:
        super().__init__(parent)
        self._unique_value = unique_value
        self._msgbox: QMessageBox | None = None
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._list = QListWidget(self)
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._list)

        controls = QHBoxLayout()
        self._input = QLineEdit(self)
        if placeholder:
            self._input.setPlaceholderText(placeholder)
        self._input.returnPressed.connect(self._add_pressed)
        controls.addWidget(self._input)
        self._add_button = QPushButton("Add", self)
        self._add_button.clicked.connect(self._add_pressed)
        controls.addWidget(self._add_button)
        self._remove_button = QPushButton("Remove", self)
        self._remove_button.clicked.connect(self._remove_pressed)
        controls.addWidget(self._remove_button)
        layout.addLayout(controls)
        self.setLayout(layout)

    def values(self) -> list[str]:
        return [self._list.item(i).text() for i in range(self._list.count())]

    def set_values(self, values: list[str]) -> None:
        self._list.clear()
        for value in values:
            self._list.addItem(value)

    def clear(self) -> None:
        self._list.clear()

    def _add_pressed(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        if self._unique_value is not None and text == self._unique_value and \
                any(v == self._unique_value for v in self.values()):
            self._msgbox = QMessageBox(
                QMessageBox.Icon.Warning, "Duplicate entry",
                f"Only one entry may contain '{self._unique_value}'.",
                QMessageBox.StandardButton.Ok, self,
            )
            self._msgbox.open()
            return
        self._list.addItem(text)
        self._input.clear()

    def _remove_pressed(self) -> None:
        row = self._list.currentRow()
        if row >= 0:
            self._list.takeItem(row)


class _RouteListWidget(QWidget):
    """List of routes; each route has a destination and a gateway."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._msgbox: QMessageBox | None = None
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._list = QListWidget(self)
        self._list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._list)

        controls = QHBoxLayout()
        self._destination_input = QLineEdit(self)
        self._destination_input.setPlaceholderText("destination, e.g. 10.0.0.0/8")
        self._destination_input.returnPressed.connect(self._add_pressed)
        controls.addWidget(self._destination_input)
        self._gateway_input = QLineEdit(self)
        self._gateway_input.setPlaceholderText("gateway, e.g. 192.168.1.1")
        self._gateway_input.returnPressed.connect(self._add_pressed)
        controls.addWidget(self._gateway_input)
        self._add_button = QPushButton("Add", self)
        self._add_button.clicked.connect(self._add_pressed)
        controls.addWidget(self._add_button)
        self._remove_button = QPushButton("Remove", self)
        self._remove_button.clicked.connect(self._remove_pressed)
        controls.addWidget(self._remove_button)
        layout.addLayout(controls)
        self.setLayout(layout)

    def values(self) -> list[dict]:
        result = []
        for i in range(self._list.count()):
            data = self._list.item(i).data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                result.append({"destination": data.get("destination", ""),
                               "gateway": data.get("gateway", "")})
        return result

    def set_values(self, values: list[dict]) -> None:
        self._list.clear()
        for value in values:
            if not isinstance(value, dict):
                continue
            self._append(str(value.get("destination", "")), str(value.get("gateway", "")))

    def clear(self) -> None:
        self._list.clear()

    def _append(self, destination: str, gateway: str) -> None:
        item = QListWidgetItem(f"{destination}  via  {gateway}")
        item.setData(Qt.ItemDataRole.UserRole, {"destination": destination, "gateway": gateway})
        self._list.addItem(item)

    def _add_pressed(self) -> None:
        destination = self._destination_input.text().strip()
        gateway = self._gateway_input.text().strip()
        if not destination or not gateway:
            self._msgbox = QMessageBox(
                QMessageBox.Icon.Warning, "Incomplete route",
                "A route needs both a destination and a gateway.",
                QMessageBox.StandardButton.Ok, self,
            )
            self._msgbox.open()
            return
        self._append(destination, gateway)
        self._destination_input.clear()
        self._gateway_input.clear()

    def _remove_pressed(self) -> None:
        row = self._list.currentRow()
        if row >= 0:
            self._list.takeItem(row)


class _InterfaceWidget(QGroupBox):
    """A single network interface configuration."""

    def __init__(self, parent: QWidget | None = None, name: str = "") -> None:
        super().__init__(parent)
        self.setTitle(name or "Interface")
        layout = QFormLayout()

        self._name_edit = QLineEdit(self)
        self._name_edit.setText(name)
        self._name_edit.textChanged.connect(self._name_changed)
        layout.addRow("Name", self._name_edit)

        self._ip_list = _StringListWidget(
            self, placeholder="IP address or AUTOMATIC", unique_value=_AUTOMATIC_IP,
        )
        layout.addRow("IP Addresses", self._ip_list)

        self._mtu_box = QSpinBox(self)
        self._mtu_box.setRange(68, 65535)
        self._mtu_box.setValue(1500)
        layout.addRow("MTU", self._mtu_box)

        self._routes_list = _RouteListWidget(self)
        layout.addRow("Routes", self._routes_list)

        self.setLayout(layout)

    def _name_changed(self, text: str) -> None:
        self.setTitle(text or "Interface")

    @property
    def interface_name(self) -> str:
        return self._name_edit.text().strip()

    def to_dict(self) -> dict:
        result: dict = {
            "addresses": self._ip_list.values(),
            "mtu": self._mtu_box.value(),
        }
        routes = self._routes_list.values()
        if routes:
            result["routes"] = routes
        return result

    def load_dict(self, data: dict) -> None:
        self._ip_list.set_values([str(v) for v in data.get("addresses", [])])
        try:
            self._mtu_box.setValue(int(data.get("mtu", 1500)))
        except (TypeError, ValueError):
            self._mtu_box.setValue(1500)
        self._routes_list.set_values(list(data.get("routes", [])))


class NetworkSettingsTab(QWidget):
    """A widget to control the network settings of a show file."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the network settings tab."""
        super().__init__(parent)
        self._show: BoardConfiguration | None = None
        self._interface_widgets: list[_InterfaceWidget] = []

        outer_layout = QVBoxLayout()
        self._enabled_checkbox = QCheckBox("Use show file specific network settings", self)
        self._enabled_checkbox.toggled.connect(self._settings_container_enabled)
        outer_layout.addWidget(self._enabled_checkbox)

        self._settings_container = QWidget(self)
        layout = QFormLayout()
        self._default_gateway_textbox: QLineEdit = QLineEdit(self)
        layout.addRow("Default Gateway", self._default_gateway_textbox)

        self._name_servers_list = _StringListWidget(self, placeholder="e.g. 1.1.1.1")
        layout.addRow("Name Servers", self._name_servers_list)

        interfaces_container = QWidget(self)
        interfaces_outer = QVBoxLayout()
        interfaces_outer.setContentsMargins(0, 0, 0, 0)
        self._interfaces_area = QScrollArea(self)
        self._interfaces_area.setWidgetResizable(True)
        self._interfaces_inner = QWidget()
        self._interfaces_layout = QVBoxLayout()
        self._interfaces_layout.addStretch()
        self._interfaces_inner.setLayout(self._interfaces_layout)
        self._interfaces_area.setWidget(self._interfaces_inner)
        interfaces_outer.addWidget(self._interfaces_area)

        interface_buttons = QHBoxLayout()
        self._add_interface_button = QPushButton("Add Interface", self)
        self._add_interface_button.clicked.connect(self._add_interface_pressed)
        interface_buttons.addWidget(self._add_interface_button)
        self._remove_interface_button = QPushButton("Remove Last Interface", self)
        self._remove_interface_button.clicked.connect(self._remove_interface_pressed)
        interface_buttons.addWidget(self._remove_interface_button)
        interface_buttons.addStretch()
        interfaces_outer.addLayout(interface_buttons)
        interfaces_container.setLayout(interfaces_outer)
        layout.addRow("Interfaces", interfaces_container)

        self._settings_container.setLayout(layout)
        outer_layout.addWidget(self._settings_container)
        self.setLayout(outer_layout)
        self._settings_container_enabled(False)

    def _settings_container_enabled(self, enabled: bool) -> None:
        self._settings_container.setEnabled(enabled)

    def _add_interface_pressed(self) -> None:
        self._append_interface(_InterfaceWidget(self._interfaces_inner))

    def _remove_interface_pressed(self) -> None:
        if not self._interface_widgets:
            return
        widget = self._interface_widgets.pop()
        self._interfaces_layout.removeWidget(widget)
        widget.deleteLater()

    def _append_interface(self, widget: _InterfaceWidget) -> None:
        self._interfaces_layout.insertWidget(self._interfaces_layout.count() - 1, widget)
        self._interface_widgets.append(widget)

    def _clear_interfaces(self) -> None:
        for widget in self._interface_widgets:
            self._interfaces_layout.removeWidget(widget)
            widget.deleteLater()
        self._interface_widgets.clear()

    def load_show_file(self, new_show: BoardConfiguration | None) -> None:
        """Load the settings from the show file."""
        self._show = new_show
        self._default_gateway_textbox.clear()
        self._name_servers_list.clear()
        self._clear_interfaces()
        if new_show is None:
            self._enabled_checkbox.setChecked(False)
            return
        self._enabled_checkbox.setChecked(
            new_show.ui_hints.get("network-config-enabled", "false").lower() == "true",
        )
        config = json.loads(new_show.ui_hints.get("network-config", "{}"))
        self._default_gateway_textbox.setText(config.get("dw", ""))
        self._name_servers_list.set_values([str(v) for v in config.get("dns", [])])
        for key, entry in config.items():
            if key in ("dw", "dns") or not isinstance(entry, dict):
                continue
            widget = _InterfaceWidget(self._interfaces_inner, name=key)
            widget.load_dict(entry)
            self._append_interface(widget)
        if not self._interface_widgets:
            for name in _detect_ethernet_interfaces():
                widget = _InterfaceWidget(self._interfaces_inner, name=name)
                widget.load_dict({"addresses": [_AUTOMATIC_IP]})
                self._append_interface(widget)

    def apply(self) -> None:
        """Apply the current dialed in settings."""
        if self._show is None:
            return
        config: dict = {
            "dw": self._default_gateway_textbox.text(),
            "dns": self._name_servers_list.values(),
        }
        for widget in self._interface_widgets:
            name = widget.interface_name
            if not name:
                continue
            config[name] = widget.to_dict()
        config_str = json.dumps(config)
        self._show.ui_hints["network-config"] = config_str
        self._show.ui_hints["network-config-enabled"] = (
            "true" if self._enabled_checkbox.isChecked() else "false"
        )
        apply_network_settings_and_notify(config_str)
