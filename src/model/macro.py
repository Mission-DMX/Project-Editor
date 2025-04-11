class Trigger:
    def __init__(self, description: str):
        self._macro: "Macro" | None = None
        # TODO parse description
        pass  # TODO implement something that can be automatically invoked based on events

    # TODO implement the __hash__ method

    def copy(self) -> "Trigger":
        raise NotImplemented()  # TODO

    def enable(self):
        """Enable the trigger on its macro (which must be set)"""
        if self._macro is not None:
            self._macro._triggers[self] = True

    def disable(self):
        """Disable the trigger on its macro (which must be set)"""
        if self._macro is not None:
            self._macro._triggers[self] = False

class Macro:
    def __init__(self):
        """Initialize a new empty macro"""
        self.content: str = ""
        self.name: str = ""
        self._triggers: dict[Trigger, bool] = {}

    @property
    def trigger_conditions(self) -> list[Trigger]:
        """Get a list of all active triggers.
        :returns: A copy of the active trigger list"""
        l = []
        for k, v in self._triggers:
            if v:
                l.append(k)
        return l

    def add_trigger(self, t: Trigger, active: bool = True):
        """
        Register a new trigger.

        :param t: The trigger to add
        :param active: Should the new trigger be active by default?
        """
        self._triggers[t] = active

    def copy(self) -> "Macro":
        """Obtain a deep copy of this macro"""
        m = Macro()
        m.name = str(self.name)
        m.content = str(self.content)
        for k, v in self._triggers:
            m._triggers[k.copy()] = bool(v)
        return m
