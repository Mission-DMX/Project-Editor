"""Event model classes."""

from __future__ import annotations

from logging import getLogger

import proto.Events_pb2
from controller.network import NetworkManager
from model import Broadcaster
from proto.Events_pb2 import event_type as prot_event_type

logger = getLogger(__name__)

_broadcaster_instance: Broadcaster = Broadcaster()
_network_manager: NetworkManager = NetworkManager()
_senders: dict[str, proto.Events_pb2.event_sender] = {}
_senders_by_id: dict[int, proto.Events_pb2.event_sender] = {}
_persistence_notes: dict[str, dict[tuple[int, int, str], str]] = {}


def handle_incoming_sender_update(msg: proto.Events_pb2.event_sender) -> None:
    """Update the sender model based on a message from fish.

    Args:
        msg: The message to use.

    """
    ev = _senders.get(msg.name)
    if ev is None:
        match msg.type:
            case "fish.builtin.plain" | "undef":
                ev = EventSender(msg.name)
            case "fish.builtin.midi":
                raise NotImplementedError
            case "fish.builtin.midirtp":
                raise NotImplementedError
            case "fish.builtin.xtouchgpio":
                ev = XtouchGPIOEventSender(msg.name)
            case "fish.builtin.gpio":
                raise NotImplementedError
            case "fish.builtin.macrokeypad":
                raise NotImplementedError
            case "fish.builtin.audioextract":
                ev = AudioExtractEventSender(msg.name)
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


_broadcaster_instance.event_sender_update.connect(handle_incoming_sender_update)


class EventSender:
    """Base class for fish event sender representations.

    Also used for fish.builtin.plain.
    """

    def __init__(self, name: str) -> None:
        """Create a new event sender.

        :param name: The name to give it. This cannot be changed later on.
        """
        self._name: str = name
        self.index_on_fish: int = -1
        self.type: str = ""
        self._debug_enabled: bool = False
        self.debug_include_ongoing_events: bool = False
        self.configuration: dict[str, str] = {}
        self.persistent: bool = False
        self.renamed_events: dict[tuple[int, int, str], str] = {}

    @property
    def name(self) -> str:
        """The human-readable name of the event sender.

        This should be unique as it is possible to search for senders by name.
        """
        return self._name

    @property
    def debug_enabled(self) -> bool:
        """Enable or disable debug logging of events."""
        return self._debug_enabled

    @debug_enabled.setter
    def debug_enabled(self, new_state: bool) -> None:
        if self._debug_enabled != new_state:
            self._debug_enabled = bool(new_state)
            self.send_update()

    # TODO implement event function and argument renaming model

    def send_update(self, auto_commit: bool = True, push_direct: bool = False) -> proto.Events_pb2.event_sender:
        """Assemble an event_sender message and publish it if auto_commit is enabled.

        While it is possible to override this method, implementing classes should
        prefer only updating the configuration parameter.

        Args:
            auto_commit: Whether the message should be sent directly.
            push_direct: Whether the message should be sent directly to fish.

        Returns:
            The assembled (and possibly sent) message.

        """
        msg = proto.Events_pb2.event_sender()
        msg.name = self.name
        if self.index_on_fish != -1:
            msg.sender_id = self.index_on_fish
        msg.type = self.type
        msg.gui_debug_enabled = self._debug_enabled
        msg.configuration.update(self.configuration)
        if auto_commit:
            _network_manager.send_event_sender_update(msg, push_direct=push_direct)
        return msg


def get_sender(name: str) -> EventSender | None:
    """Look up a specific sender by its name.

    Args:
        name: The unique name of the sender.

    Returns:
        The sender object if the lookup was successful.

    """
    return _senders.get(name)


def get_sender_by_id(sender_id: int) -> EventSender | None:
    """Get the event sender by its index on fish."""
    return _senders_by_id.get(sender_id)


def get_all_senders() -> list[proto.Events_pb2.event_sender]:
    """Get a list of all senders currently running on fish.

    Returns:
        list: A mutable list (copied).

    """
    return list(_senders.values())


class XtouchGPIOEventSender(EventSender):
    """Event sender reacting on the pedal GPIO input of a connected X-Touch."""

    def __init__(self, name: str) -> None:
        """Initialize a new Xtouch GPIO event sender."""
        super().__init__(name)

    @property
    def pedal_threshold(self) -> int:
        """Trigger threshold of the pedal."""
        return int(self.configuration.get("expression_pedal_threshold") or "0")

    @pedal_threshold.setter
    def pedal_threshold(self, new_value: int) -> None:
        self.configuration["expression_pedal_threshold"] = str(new_value)


class AudioExtractEventSender(EventSender):
    """Event sender using audio beat analysis to trigger events."""

    def __init__(self, name: str) -> None:
        """Initialize the event sender."""
        super().__init__(name)

    @property
    def audio_device(self) -> str:
        """The alsa device node or pulse device name."""
        return self.configuration.get("dev") or "default"

    @audio_device.setter
    def audio_device(self, new_value: str) -> None:
        self.configuration["dev"] = new_value

    @property
    def high_cut(self) -> int:
        """High cutoff frequency of beat detection."""
        return int(self.configuration.get("high_cut") or "100")

    @high_cut.setter
    def high_cut(self, new_value: int) -> None:
        self.configuration["high_cut"] = str(new_value)

    @property
    def low_cut(self) -> int:
        """Low cutoff frequency of beat detection."""
        return int(self.configuration.get("low_cut") or "10")

    @low_cut.setter
    def low_cut(self, new_value: int) -> None:
        self.configuration["low_cut"] = str(new_value)

    @property
    def magnitude(self) -> float:
        """Trigger magnitude of beat detection."""
        return float(self.configuration.get("magnitude") or "10")

    @magnitude.setter
    def magnitude(self, new_value: float) -> None:
        self.configuration["magnitude"] = str(new_value)


def insert_event(
    sender_id: int, sender_function: int = 0, event_type: str = "single", arguments: list[int] | None = None
) -> None:
    """Insert an event in fish.

    Args:
        sender_id: The id of the sender the event is supposed to be originating from.
            Supplying a negative value will abort the action.
        sender_function: The event sender function to use.
        event_type: The event type to use. Must be one of "single", "release" or "start".
        arguments: The event arguments to use.

    """
    if sender_id < 0:
        return
    if event_type not in ["single", "release", "start"]:
        raise ValueError(f"Unsupported event type. Must be one of single, release or start but is '{event_type}'.")
    if arguments is None:
        arguments = []

    ev = proto.Events_pb2.event()
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


def mark_sender_persistent(name: str, renaming: dict[tuple[int, int, str], str] | None = None) -> None:
    """Mark an event sender as persistent.

    If the event sender is not yet known, it will be marked once it is announced to the editor.

    Args:
    name: The unique name of the sender.
    renaming: The renaming data indicator of the sender. It will be noted as well.

    """
    if renaming is None:
        renaming = {}
    sender = get_sender(name)
    if sender is not None:
        sender.persistent = True
        sender.renamed_events.update(renaming)
    else:
        _persistence_notes[name] = renaming.copy()
