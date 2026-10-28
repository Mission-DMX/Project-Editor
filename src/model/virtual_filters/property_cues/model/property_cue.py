"""Property-based cue: an ordered list of steps with a name."""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger

from model.virtual_filters.property_cues.model.property_step import PropertyStep

logger = getLogger(__name__)


_VALID_END_ACTIONS = frozenset({"hold", "start_again", "next_cue"})


@dataclass(slots=True)
class PropertyCue:
    name: str = "Cue 1"
    steps: list[PropertyStep] = field(default_factory=list)
    end_action: str = "hold"
    restart_on_play: bool = False

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "steps": [step.to_json() for step in self.steps],
            "end_action": self.end_action,
            "restart_on_play": self.restart_on_play,
        }

    @classmethod
    def from_json(cls, blob: dict) -> PropertyCue:
        steps_blob = blob.get("steps", []) or []
        steps = [PropertyStep.from_json(step_blob) for step_blob in steps_blob]
        end_action = blob.get("end_action", "hold")
        if end_action not in _VALID_END_ACTIONS:
            end_action = "hold"
        return cls(
            name=blob.get("name", "Cue 1"),
            steps=steps,
            end_action=end_action,
            restart_on_play=bool(blob.get("restart_on_play", False)),
        )
