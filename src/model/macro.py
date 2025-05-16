from logging import getLogger

from PySide6.QtCore import QObject, Signal

from controller.utils.process_notifications import get_process_notifier
from proto.Console_pb2 import ButtonCode, ButtonState, button_state_change

logger = getLogger(__file__)


def trigger_factory(trigger_type: str):
    match trigger_type:
        case "startup":
            return _StartupTrigger()
        case "f_keys":
            return _FKeysTrigger()
        case _:
            raise ValueError("Unsupported trigger type")


class Trigger(QObject):

    SUPPORTED_TYPES = ["startup", "f_keys"]

    enabled_changed: Signal = Signal(bool)

    def __init__(self, tr_t: str):
        super().__init__()
        self._macro: "Macro" | None = None
        self._type: str = tr_t
        self.name: str = ""
        self._configuration: dict[str, str] = {}

    def copy(self) -> "Trigger":
        t = trigger_factory(self._type)
        t.name = self.name
        for k, v in self._configuration.items():
            t.set_param(k, v)
        return t

    @property
    def enabled(self) -> bool:
        if self._macro is not None:
            return self._macro._triggers[self]
        else:
            return False

    @enabled.setter
    def enabled(self, new_state: bool):
        """Enable or disable the trigger on its macro (which must be set)"""
        if self._macro is not None:
            self._macro._triggers[self] = new_state
            self.enabled_changed.emit(new_state)

    def set_param(self, key: str, value: str):
        self._configuration[key] = value

    @property
    def configuration(self) -> dict[str, str]:
        return self._configuration.copy()

    @property
    def type(self) -> str:
        return self._type

    def exec(self):
        if self._macro is not None:
            pn = get_process_notifier(f"Macro: {self._macro.name}, triggered by {self.name}", 1)
            pn.current_step_description = "Inferencing macro"
            self._macro.exec()
            pn.current_step_number = 1
            pn.close()


class _StartupTrigger(Trigger):

    def __init__(self):
        super().__init__("startup")
        from model import Broadcaster
        Broadcaster().board_configuration_loaded.connect(self.exec)

class _FKeysTrigger(Trigger):
    def __init__(self):
        super().__init__("f_keys")
        self._key: int = 0
        self.set_param("button", "0")
        from model import Broadcaster
        Broadcaster().desk_f_key_pressed.connect(self._key_pressed)

    def _key_pressed(self, key: int):
        if key == self._key:
            self.exec()

    def set_param(self, key: str, value: str):
        super().set_param(key, value)
        if key == "button":
            new_value = int(value)
            if new_value > 7 or new_value < 0:
                raise ValueError("F Buttons range from 0 to 7")
            self._key = new_value
            from controller.network import NetworkManager
            msg = button_state_change(
                button=ButtonCode.Value(f"BTN_F{new_value + 1}_F{new_value + 1}"),
                new_state=ButtonState.BS_ACTIVE
            )
            NetworkManager().button_msg_to_x_touch(msg)


class Macro:
    def __init__(self, parent: "BoardConfiguration"):
        """Initialize a new empty macro"""
        self.content: str = ""
        self.name: str = ""
        self._show: "BoardConfiguration" = parent
        self._triggers: dict[Trigger, bool] = {}
        from controller.cli.cli_context import CLIContext
        from controller.network import NetworkManager
        self.c = CLIContext(self._show, NetworkManager(), exit_available=False)

    @property
    def trigger_conditions(self) -> list[Trigger]:
        """Get a list of all active triggers.
        :returns: A copy of the active trigger list"""
        l = []
        for k, v in self._triggers:
            if v:
                l.append(k)
        return l

    @property
    def all_triggers(self) -> list[Trigger]:
        return list(self._triggers.keys())

    def add_trigger(self, t: Trigger, active: bool = True):
        """
        Register a new trigger.

        :param t: The trigger to add
        :param active: Should the new trigger be active by default?
        """
        t = t.copy()
        self._triggers[t] = active
        t._macro = self

    def copy(self) -> "Macro":
        """Obtain a deep copy of this macro"""
        m = Macro(self._show)
        m.name = str(self.name)
        m.content = str(self.content)
        for k, v in self._triggers:
            m._triggers[k.copy()] = bool(v)
        return m

    def exec(self) -> bool:
        success = True
        for l in self.content.split("\n"):
            if not self.c.exec_command(l):
                success = False
                logger.error("Failed to execute command: %s", l)
        return success
