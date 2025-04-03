from logging import getLogger
from typing import TYPE_CHECKING

from proto.Events_pb2 import event_sender

if TYPE_CHECKING:
    from controller.network import NetworkManager
    from model import Broadcaster

logger = getLogger(__file__)

_broadcaster_instance: "Broadcaster"
_network_manager: "NetworkManager"
_senders: dict[str, "EventSender"] = {}


def set_broadcaster_and_network(b: "Broadcaster", nm: "NetworkManager"):
    """Set the broadcasting instance"""
    global _broadcaster_instance
    _broadcaster_instance = b
    global _network_manager
    _network_manager = nm
    logger.debug("Successfully set up network and signal broadcaster")
    return _handle_incoming_sender_update


def _handle_incoming_sender_update(msg: "event_sender"):
    """Update the sender model based on the provided message from fish.
    :param msg: The message to use"""
    global _broadcaster_instance
    global _senders
    ev = _senders.get(msg.name)
    if ev is None:
        match msg.type:
            case "fish.builtin.plain":
                ev = EventSender(msg.name)
            case "fish.builtin.midi":
                raise NotImplemented()
            case "fish.builtin.midirtp":
                raise NotImplemented()
            case "fish.builtin.xtouchgpio":
                ev = XtouchGPIOEventSender(msg.name)
            case "fish.builtin.gpio":
                raise NotImplemented()
            case "fish.builtin.macrokeypad":
                raise NotImplemented()
        _senders[msg.name] = ev
    ev.index_on_fish = msg.sender_id
    ev.debug_enabled = msg.gui_debug_enabled
    ev.configuration.update(msg.configuration)
    if _broadcaster_instance is not None:
        _broadcaster_instance.event_sender_model_updated.emit()


class EventSender:
    """Base class for fish event sender representations. Also used for fish.builtin.plain"""
    def __init__(self, name: str):
        """Create a new event sender.
        :param name: The name to give it. This cannot be changed later on."""
        self._name: str = name
        self.index_on_fish: int = -1
        self.type: str = ""
        self._debug_enabled: bool = False
        self.configuration: dict[str, str] = dict()

    @property
    def name(self) -> str:
        return self._name

    @property
    def debug_enabled(self) -> bool:
        return self._debug_enabled

    @debug_enabled.setter
    def debug_enabled(self, new_state: bool):
        self._debug_enabled = bool(new_state)
        self.send_update()

    # TODO implement event function and argument renaming model

    def send_update(self, auto_commit: bool = True) -> event_sender:
        """
        Assemble an event_sender message and publish it if auto_commit is enabled.
        While it is possible to override this method, it is advisable to implementing classes
        to only update the configuration parameter.
        :param auto_commit: Should the message be sent directly?
        :returns: The assembled (and perhaps sent) message
        """
        msg = event_sender()
        msg.name = self.name
        msg.sender_id = self.index_on_fish
        msg.type = self.type
        msg.gui_debug_enabled = self._debug_enabled
        msg.configuration.update(self.configuration)
        if auto_commit:
            global _network_manager
            _network_manager.send_event_sender_update(msg)
        return msg


def get_sender(name: str) -> EventSender | None:
    """
    Look up a specific sender by its name.
    :param name: The unique name of the sender
    :returns: the object if the lookup was successful
    """
    return _senders.get(name)


def get_all_senders() -> list[EventSender]:
    """
    Get a list of all sender currently running on fish.
    :returns: A mutable list (copied)
    """
    return list(_senders.values())


class XtouchGPIOEventSender(EventSender):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def pedal_threshold(self) -> int:
        return int(self.configuration.get("expression_pedal_threshold") or "0")

    @pedal_threshold.setter
    def pedal_threshold(self, new_value: int):
        self.configuration["expression_pedal_threshold"] = str(new_value)
