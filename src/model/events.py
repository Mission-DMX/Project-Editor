from logging import getLogger
from typing import TYPE_CHECKING

from controller.network import NetworkManager
from model import Broadcaster

if TYPE_CHECKING:
    from proto.Events_pb2 import event_sender

logger = getLogger(__file__)

_broadcaster_instance: Broadcaster | None = None
_senders: dict[str, "event_sender"] = {}


def set_broadcaster_and_network(b: Broadcaster, nm: NetworkManager):
    """Set the broadcasting instance"""
    global _broadcaster_instance
    _broadcaster_instance = b
    nm.sender_message_callback = _handle_incoming_sender_update
    logger.debug("Successfully set up network and signal broadcaster")


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
        self.debug_enabled: bool = False
        self.configuration: dict[str, str] = dict()

    # TODO implement event function and argument renaming model
