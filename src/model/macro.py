from logging import getLogger

from model import Broadcaster

logger = getLogger(__file__)

class Trigger:

    def __new__(cls, trigger_type: str):
        match trigger_type:
            case "startup":
                return _StartupTrigger()
            # TODO implement trigger for macro listening
            case _:
                raise ValueError("Unsupported trigger type")

    def __init__(self, tr_t: str):
        self._macro: "Macro" | None = None
        self._type: str = tr_t
        self.name: str = ""
        self._configuration: dict[str, str] = {}
        pass  # TODO implement something that can be automatically invoked based on events

    # TODO implement the __hash__ method

    def copy(self) -> "Trigger":
        raise NotImplemented()  # TODO

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
            self._macro.exec()


class _StartupTrigger(Trigger):

    def __new__(cls):
        return object.__new__(cls)

    def __init__(self):
        super().__init__("startup")
        Broadcaster().board_configuration_loaded.connect(self.exec)


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
                logger.error(f"Failed to execute command: {l}")
        return success
