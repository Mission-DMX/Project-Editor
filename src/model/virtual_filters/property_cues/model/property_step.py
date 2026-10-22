"""Step-level model: per-node property assignments plus step metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger
from typing import Any

from model.color_hsi import ColorHSI
from model.virtual_filters.property_cues.distribution import Distribution, DistributionMethod

logger = getLogger(__name__)


def _distribution_to_json(dist: Distribution) -> dict:
    return {
        "method": dist.method.value,
        "phase_offset": dist.phase_offset,
        "amplitude": dist.amplitude,
        "introduction_delay_only": dist.introduction_delay_only,
    }


def _distribution_from_json(blob: dict) -> Distribution:
    return Distribution(
        method=DistributionMethod(blob.get("method", DistributionMethod.CONSTANT.value)),
        phase_offset=float(blob.get("phase_offset", 0.0)),
        amplitude=float(blob.get("amplitude", 1.0)),
        introduction_delay_only=bool(blob.get("introduction_delay_only", False)),
    )


def _value_to_json(value: Any) -> Any:
    if isinstance(value, ColorHSI):
        return {"__kind__": "color_hsi", "value": value.format_for_filter()}
    if isinstance(value, dict):
        return {k: _value_to_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_value_to_json(v) for v in value]
    return value


def _value_from_json(blob: Any) -> Any:
    if isinstance(blob, dict):
        if blob.get("__kind__") == "color_hsi":
            return ColorHSI.from_filter_str(blob["value"], strict=True)
        return {k: _value_from_json(v) for k, v in blob.items()}
    if isinstance(blob, list):
        return [_value_from_json(v) for v in blob]
    return blob


@dataclass(slots=True)
class ManualPropertyAssignment:
    """User-dialed manual property values plus a distribution."""
    values: dict[str, Any]
    distribution: Distribution = field(default_factory=Distribution)
    transition: str = "lin"

    def to_json(self) -> dict:
        return {
            "mode": "manual",
            "value": {k: _value_to_json(v) for k, v in self.values.items()},
            "distribution": _distribution_to_json(self.distribution),
            "transition": self.transition,
        }

    @classmethod
    def from_json(cls, blob: dict) -> ManualPropertyAssignment:
        raw_values = blob.get("value", {}) or {}
        values = {k: _value_from_json(v) for k, v in raw_values.items()}
        distribution = _distribution_from_json(blob.get("distribution", {}))
        transition = blob.get("transition", "lin")
        return cls(values=values, distribution=distribution, transition=transition)


@dataclass(slots=True)
class PresetPropertyAssignment:
    preset_id: str
    hint_values: dict[str, Any] = field(default_factory=dict)
    distribution: Distribution = field(default_factory=Distribution)

    def to_json(self) -> dict:
        return {
            "mode": "preset",
            "preset_id": self.preset_id,
            "hint_values": {k: _value_to_json(v) for k, v in self.hint_values.items()},
            "distribution": _distribution_to_json(self.distribution),
        }

    @classmethod
    def from_json(cls, blob: dict) -> PresetPropertyAssignment:
        raw_hints = blob.get("hint_values", {}) or {}
        hint_values = {k: _value_from_json(v) for k, v in raw_hints.items()}
        return cls(
            preset_id=blob["preset_id"],
            hint_values=hint_values,
            distribution=_distribution_from_json(blob.get("distribution", {})),
        )


PropertyAssignment = ManualPropertyAssignment | PresetPropertyAssignment


def _assignment_from_json(blob: dict) -> PropertyAssignment:
    mode = blob.get("mode")
    if mode == "manual":
        return ManualPropertyAssignment.from_json(blob)
    if mode == "preset":
        return PresetPropertyAssignment.from_json(blob)
    raise ValueError(f"Unknown assignment mode: {mode!r}")


@dataclass(slots=True)
class PropertyAssignments:
    """Map from property_id ("dimmer", "position", ...) to an assignment for a single node."""
    by_property: dict[str, PropertyAssignment] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {prop_id: assignment.to_json() for prop_id, assignment in self.by_property.items()}

    @classmethod
    def from_json(cls, blob: dict) -> PropertyAssignments:
        by_property: dict[str, PropertyAssignment] = {}
        for prop_id, assignment_blob in blob.items():
            by_property[prop_id] = _assignment_from_json(assignment_blob)
        return cls(by_property=by_property)


@dataclass(slots=True)
class PropertyStep:
    name: str = ""
    duration_40hz: int = 40
    fade_in_40hz: int = 0
    assignments: dict[str, PropertyAssignments] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "duration_40hz": self.duration_40hz,
            "fade_in_40hz": self.fade_in_40hz,
            "assignments": {
                node_path: node_assignments.to_json()
                for node_path, node_assignments in self.assignments.items()
            },
        }

    @classmethod
    def from_json(cls, blob: dict) -> PropertyStep:
        assignments_blob = blob.get("assignments", {}) or {}
        assignments = {
            node_path: PropertyAssignments.from_json(node_blob)
            for node_path, node_blob in assignments_blob.items()
        }
        return cls(
            name=blob.get("name", ""),
            duration_40hz=int(blob.get("duration_40hz", 40)),
            fade_in_40hz=int(blob.get("fade_in_40hz", 0)),
            assignments=assignments,
        )
