from logging import getLogger
from typing import TYPE_CHECKING

from proto.Events_pb2 import event, event_sender
from proto.Events_pb2 import event_type as prot_event_type

if TYPE_CHECKING:
    from controller.network import NetworkManager
    from model import Broadcaster

logger = getLogger(__file__)

_broadcaster_instance: "Broadcaster"
_network_manager: "NetworkManager"
_senders: dict[str, "EventSender"] = {}
_senders_by_id: dict[int, "EventSender"] = {}
_persistence_notes: dict[str, dict[tuple[int, int, str], str]] = {}


def set_broadcaster_and_network(b: "Broadcaster", nm: "NetworkManager"):
    """Set the broadcasting instance"""
    global _broadcaster_instance
    _broadcaster_instance = b
    global _network_manager
    _network_manager = nm
    logger.debug("Successfully set up network and signal broadcaster")
    return _handle_incoming_sender_update


def _handle_incoming_sender_update(msg: "event_sender") -> None:
    """Update the sender model based on the provided message from fish.
    :param msg: The message to use"""
    global _broadcaster_instance
    global _senders
    ev = _senders.get(msg.name)
    if ev is None:
        match msg.type:
            case "fish.builtin.plain" | "undef":
                ev = EventSender(msg.name)
            case "fish.builtin.midi":
                raise NotImplementedError()
            case "fish.builtin.midirtp":
                raise NotImplementedError()
            case "fish.builtin.xtouchgpio":
                ev = XtouchGPIOEventSender(msg.name)
            case "fish.builtin.gpio":
                raise NotImplementedError()
            case "fish.builtin.macrokeypad":
                raise NotImplementedError()
            case _:
                logger.error("Unexpaected event sender type: '%s'", msg.type)
                return
        _senders[msg.name] = ev
        _senders_by_id[msg.sender_id] = ev
        ev.type = msg.type
        pnote = _persistence_notes.get(msg.name)
        if pnote is not None:
            ev.renamed_events.update(pnote)
            _persistence_notes.pop(msg.name)
            ev.persistent = True
    ev.index_on_fish = msg.sender_id
    ev.debug_enabled = msg.gui_debug_enabled
    ev.configuration.update(msg.configuration)
    if _broadcaster_instance is not None:
        _broadcaster_instance.event_sender_model_updated.emit()


class EventSender:
    """Base class for fish event sender representations. Also used for fish.builtin.plain"""

    def __init__(self, name: str) -> None:
        """Create a new event sender.
        :param name: The name to give it. This cannot be changed later on."""
        self._name: str = name
        self.index_on_fish: int = -1
        self.type: str = ""
        self._debug_enabled: bool = False
        self.debug_include_ongoing_events: bool = False
        self.configuration: dict[str, str] = dict()
        self.persistent: bool = False
        self.renamed_events: dict[tuple[int, int, str], str] = dict()

    @property
    def name(self) -> str:
        return self._name

    @property
    def debug_enabled(self) -> bool:
        return self._debug_enabled

    @debug_enabled.setter
    def debug_enabled(self, new_state: bool) -> None:
        if self._debug_enabled != new_state:
            self._debug_enabled = bool(new_state)
            self.send_update()

    # TODO implement event function and argument renaming model

    def send_update(self, auto_commit: bool = True, push_direct: bool = False) -> event_sender:
        """
        Assemble an event_sender message and publish it if auto_commit is enabled.
        While it is possible to override this method, it is advisable to implementing classes
        to only update the configuration parameter.
        :param auto_commit: Should the message be sent directly?
        :returns: The assembled (and perhaps sent) message
        """
        msg = event_sender()
        msg.name = self.name
        if self.index_on_fish != -1:
            msg.sender_id = self.index_on_fish
        msg.type = self.type
        msg.gui_debug_enabled = self._debug_enabled
        msg.configuration.update(self.configuration)
        if auto_commit:
            global _network_manager
            _network_manager.send_event_sender_update(msg, push_direct=push_direct)
        return msg


def get_sender(name: str) -> EventSender | None:
    """
    Look up a specific sender by its name.
    :param name: The unique name of the sender
    :returns: the object if the lookup was successful
    """
    return _senders.get(name)


def get_sender_by_id(sender_id: int) -> EventSender | None:
    """Get the event sender by its index on fish."""
    return _senders_by_id.get(sender_id)


def get_all_senders() -> list[EventSender]:
    """
    Get a list of all sender currently running on fish.
    :returns: A mutable list (copied)
    """
    return list(_senders.values())


class XtouchGPIOEventSender(EventSender):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @property
    def pedal_threshold(self) -> int:
        return int(self.configuration.get("expression_pedal_threshold") or "0")

    @pedal_threshold.setter
    def pedal_threshold(self, new_value: int) -> None:
        self.configuration["expression_pedal_threshold"] = str(new_value)


def insert_event(sender_id: int, sender_function: int = 0, event_type: str = "single", arguments: list[int] = None):
    """Insert an event in fish.

    :param sender_id: The id of the sender the event is supposed to be originating from. Supplying a negative value will
    abort the action.

    :param sender_function: The event sender function to use
    :param event_type: The event type to use. Must be one of single, release or start
    :param arguments: The event arguments to use
    """
    if sender_id < 0:
        return
    if event_type not in ["single", "release", "start"]:
        raise ValueError(f"Unsupported event type. Must be one of single, release or start but is '{event_type}'.")
    if arguments is None:
        arguments = []

    ev = event()
    ev.sender_id = sender_id
    ev.sender_function = sender_function
    match event_type:
        case "single":
            ev.type = prot_event_type.SINGLE_TRIGGER
        case "start":
            ev.type = prot_event_type.START
        case "release":
            ev.type = prot_event_type.RELEASE
    ev.arguments.extend([max(min(arg, 255), 0) for arg in arguments])
    _network_manager.send_event_message(ev)


def mark_sender_persistent(name: str, renaming: dict[tuple[int, int, str], str] = None):
    if renaming is None:
        renaming = {}
    sender = get_sender(name)
    if sender is not None:
        sender.persistent = True
        sender.renamed_events.update(renaming)
    else:
        _persistence_notes[name] = renaming.copy()
