from PySide6.QtDBus import QDBus, QDBusConnection, QDBusInterface, QDBusMessage

_SERVICE = "org.mission_dmx.networking_ctrl"
_PATH = "/"
_INTERFACE = "org.mission_dmx.networking_ctrl"
_METHOD = "ApplyConfiguration"

_NOTIFICATIONS_SERVICE = "org.freedesktop.Notifications"
_NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"
_APP_NAME = "MissionDMX"


def apply_network_settings_and_notify(json: str) -> bool:
    """Apply the settings and publish a desktop notification about the outcome."""
    success, reason = _apply(json)
    _notify(success, reason)
    return success


def _apply(json: str) -> tuple[bool, str]:
    bus = QDBusConnection.systemBus()
    if not bus.isConnected():
        return False, "Could not connect to the system D-Bus."
    interface = QDBusInterface(_SERVICE, _PATH, _INTERFACE, bus)
    if not interface.isValid():
        return False, f"Service '{_SERVICE}' is not available on the system bus."
    reply = interface.call(_METHOD, json)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        return False, reply.errorMessage() or "Unknown D-Bus error."
    return True, ""


def _notify(success: bool, reason: str) -> None:
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        return
    notifications = QDBusInterface(
        _NOTIFICATIONS_SERVICE, _NOTIFICATIONS_PATH, _NOTIFICATIONS_SERVICE, bus,
    )
    if not notifications.isValid():
        return
    if success:
        summary = "Network settings applied"
        body = "The new network settings were applied successfully."
        icon = "network-transmit-receive"
    else:
        summary = "Failed to apply network settings"
        body = reason or "An unknown error occurred."
        icon = "dialog-error"
    notifications.call(
        QDBus.CallMode.NoBlock, "Notify",
        _APP_NAME, 0, icon, summary, body, [], {}, -1,
    )
