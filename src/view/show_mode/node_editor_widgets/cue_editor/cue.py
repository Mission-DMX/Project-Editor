from abc import ABC, abstractmethod
from enum import Enum

from view.show_mode.node_editor_widgets.cue_editor.utility import format_seconds


class EndAction(Enum):
    HOLD = 0
    START_AGAIN = 1
    NEXT = 2

    def __str__(self):
        if self.value == EndAction.HOLD:
            return "Hold current values"
        elif self.value == EndAction.NEXT:
            return "Jump to next cue"
        elif self.value == EndAction.START_AGAIN:
            return "Restart cue"
        else:
            return "Unknown action"

    @property
    def formatted_value_list(self) -> list[str]:
        return [str(a) for a in [EndAction.HOLD, EndAction.NEXT, EndAction.START_AGAIN]]


class State(ABC):
    @abstractmethod
    def encode(self) -> str:
        """This method returns the state encodes in the filter format"""
        raise NotImplementedError

    @abstractmethod
    def decode(self, content: str):
        """This method decodes the state configuration from a filter config string."""
        raise NotImplementedError


class KeyFrame:
    def __init__(self):
        self._states: list[State] = []


class Cue:
    def __init__(self):
        self.end_action = EndAction.HOLD
        self._frames: list[KeyFrame] = []

    @property
    def duration(self) -> float:
        """Computes the length of the cue"""
        # TODO implement
        return 0.0

    @property
    def duration_formatted(self) -> str:
        """Returns the duration of the cue as a formatted string."""
        return format_seconds(self.duration)

