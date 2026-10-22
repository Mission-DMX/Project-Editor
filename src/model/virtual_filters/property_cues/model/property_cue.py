"""Property-based cue: an ordered list of steps with a name."""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger

from model.virtual_filters.property_cues.model.property_step import PropertyStep

logger = getLogger(__name__)


@dataclass(slots=True)
class PropertyCue:
    name: str = "Cue 1"
    steps: list[PropertyStep] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "steps": [step.to_json() for step in self.steps],
        }

    @classmethod
    def from_json(cls, blob: dict) -> PropertyCue:
        steps_blob = blob.get("steps", []) or []
        steps = [PropertyStep.from_json(step_blob) for step_blob in steps_blob]
        return cls(
            name=blob.get("name", "Cue 1"),
            steps=steps,
        )
