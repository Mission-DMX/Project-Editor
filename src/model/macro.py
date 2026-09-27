"""Macros with their Triggers."""

from __future__ import annotations

from functools import lru_cache
from logging import getLogger
from typing import TYPE_CHECKING, Final

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QObject, Signal

from controller.utils.process_notifications import get_process_notifier
from proto.Console_pb2 import ButtonCode, ButtonState, button_state_change

if TYPE_CHECKING:
    from controller.cli.cli_context import CLIContext
    from model import BoardConfiguration

logger = getLogger(__name__)


def trigger_factory(trigger_type: str) -> Trigger:
    """Trigger Factory."""
    match trigger_type:
        case "startup":
            return _StartupTrigger()
        case "f_keys":
            return _FKeysTrigger()
        case "showfile_applied":
            return _ShowfileAppliedTrigger()
        case _:
            raise ValueError("Unsupported trigger type")


class Trigger(QObject):
    """Macro Trigger."""

    SUPPORTED_TYPES: Final[list[str]] = ["startup", "f_keys", "showfile_applied"]

    enabled_changed: Signal = Signal(bool)

    def __init__(self, tr_t: str) -> None:
        """Macro Trigger."""
        super().__init__()
        self._macro: Macro | None = None
        self._type: str = tr_t
        self.name: str = ""
        self._configuration: dict[str, str] = {}

    def copy(self) -> Trigger:
        """Copy a trigger."""
        t = trigger_factory(self._type)
        t.name = self.name
        for k, v in self._configuration.items():
            t.set_param(k, v)
        return t

    @property
    def enabled(self) -> bool:
        """Is macro trigger enabled."""
        if self._macro is not None:
            return self._macro._triggers[self]
        return False

    @enabled.setter
    def enabled(self, new_state: bool) -> None:
        """Enable or disable the trigger on its macro (which must be set)."""
        if self._macro is not None:
            self._macro._triggers[self] = new_state
            self.enabled_changed.emit(new_state)

    def set_param(self, key: str, value: str) -> None:
        """Set Params of a Trigger."""
        self._configuration[key] = value

    @property
    def configuration(self) -> dict[str, str]:
        """Configuration Copy of a Trigger."""
        return self._configuration.copy()

    @property
    def type(self) -> str:
        """Type of the Trigger."""
        return self._type

    def exec(self) -> None:
        """Execute a Trigger."""
        if self._macro is not None:
            pn = get_process_notifier(f"Macro: {self._macro.name}, triggered by {self.name}", 1)
            pn.current_step_description = "Inferencing macro"
            self._macro.exec()
            pn.current_step_number = 1
            pn.close()


class _StartupTrigger(Trigger):
    """Trigger on Startup."""

    def __init__(self) -> None:
        super().__init__("startup")
        from model import Broadcaster

        Broadcaster().board_configuration_loaded.connect(self.exec)


class _ShowfileAppliedTrigger(Trigger):
    """Trigger ofter successful application of show file to fish."""

    def __init__(self) -> None:
        super().__init__("showfile_applied")
        from model import Broadcaster

        Broadcaster().show_file_applied.connect(self.exec)


class _FKeysTrigger(Trigger):
    """Triggers for F-Keys."""

    def __init__(self) -> None:
        super().__init__("f_keys")
        self._key: int = 0
        self.set_param("button", "0")
        from model import Broadcaster

        Broadcaster().desk_f_key_pressed.connect(self._key_pressed)

    def _key_pressed(self, key: int) -> None:
        if key == self._key:
            self.exec()

    def set_param(self, key: str, value: str) -> None:
        """Set Params of a Trigger."""
        super().set_param(key, value)
        if key == "button":
            new_value = int(value)
            if new_value > 7 or new_value < 0:
                raise ValueError("F Buttons range from 0 to 7")
            self._key = new_value
            from controller.network import NetworkManager

            msg = button_state_change(
                button=ButtonCode.Value(f"BTN_F{new_value + 1}_F{new_value + 1}"),
                new_state=ButtonState.BS_ACTIVE,
            )
            NetworkManager().button_msg_to_x_touch(msg)


_SHARED_CONTEXT_REGISTRY: dict[BoardConfiguration, dict[str, CLIContext]] = {}


def _clear_shared_context_registry() -> None:
    """Drop all registered shared contexts.

    This method is invoked whenever a show file is (re)loaded: the complete show model is replaced, so contexts and
    the state accumulated within them (like the selected bank set) must not be reused by macros of the new file.
    """
    _SHARED_CONTEXT_REGISTRY.clear()


@lru_cache(maxsize=1)
def _ensure_registry_cleanup_connected() -> None:
    """Connect the registry cleanup to the clear_board_configuration signal.

    This function is idempotent: the connection is only established by the first call. The broadcaster is imported
    lazily in order to avoid import cycles during module initialization.
    """
    from model import Broadcaster

    Broadcaster().clear_board_configuration.connect(_clear_shared_context_registry)


def get_available_shared_context_identifiers(show: BoardConfiguration) -> list[str]:
    """Get the IDs of shared contexts available within the given show.

    Shared contexts are never shared across show configurations, so only identifiers registered for the given show
    are returned.

    Args:
        show: the show configuration to get the shared context identifiers of

    Returns:
        the ids of all shared contexts of the given show

    """
    _ensure_registry_cleanup_connected()
    return list(_SHARED_CONTEXT_REGISTRY.get(show, {}).keys())


def _get_or_create_shared_context(show: BoardConfiguration, context_id: str) -> CLIContext:
    """Get the shared CLI context of the given show identified by context_id, creating it if it does not exist.

    Args:
        show: the show configuration the context belongs to
        context_id: the identifier of the shared context

    Returns:
        the shared context of the given show with the given identifier

    """
    _ensure_registry_cleanup_connected()
    contexts = _SHARED_CONTEXT_REGISTRY.setdefault(show, {})
    context = contexts.get(context_id)
    if context is None:
        from controller.cli.cli_context import CLIContext
        from controller.network import NetworkManager

        context = CLIContext(show, NetworkManager(), exit_available=False)
        contexts[context_id] = context
    return context


class Macro:
    """Macro."""

    def __init__(self, parent: BoardConfiguration, shared_context: str | None = None) -> None:
        """Empty macro.

        Args:
            parent: The parent board configuration
            shared_context: If the macro should use a shared context, the id of it. If None (default) or a blank
                string is provided, a private context will be created.

        """
        self.content: str = ""
        self.name: str = ""
        self._show: BoardConfiguration = parent
        self._triggers: dict[Trigger, bool] = {}
        from controller.cli.cli_context import CLIContext
        from controller.network import NetworkManager

        if shared_context is not None:
            shared_context = shared_context.strip() or None
        if shared_context is None:
            self.c = CLIContext(self._show, NetworkManager(), exit_available=False)
        else:
            self.c = _get_or_create_shared_context(self._show, shared_context)
        self._shared_context_id = shared_context

    @property
    def trigger_conditions(self) -> list[Trigger]:
        """Copy list of all active triggers."""
        trigger_conditions = []
        for k, v in self._triggers.items():
            if v:
                trigger_conditions.append(k)
        return trigger_conditions

    @property
    def all_triggers(self) -> list[Trigger]:
        """All Triggers of a Macro."""
        return list(self._triggers.keys())

    @property
    def shared_context_id(self) -> str | None:
        """The shared context ID of the macro."""
        return self._shared_context_id

    def add_trigger(self, t: Trigger, active: bool = True) -> None:
        """Register a new trigger.

        Args:
            t: The trigger to add
            active: Should the new trigger be active by default?

        """
        t = t.copy()
        self._triggers[t] = active
        t._macro = self

    def copy(self) -> Macro:
        """Deep copy of this macro.

        The copy intentionally joins the same shared context as the original (if any): macros bound to a shared
        context operate on the same CLI state, so the copy must not fork it.
        """
        m = Macro(self._show, shared_context=self._shared_context_id)
        m.name = str(self.name)
        m.content = str(self.content)
        for t, active in self._triggers.items():
            m.add_trigger(t, active)
        return m

    def exec(self) -> bool:
        """Execute a Macro."""
        success = True
        for command in self.content.split("\n"):
            if not self.c.exec_command(command):
                success = False
                logger.error("Failed to execute command: %s", command)
            else:
                QtGui.QGuiApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents)
        return success
