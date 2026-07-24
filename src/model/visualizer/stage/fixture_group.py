"""Contains StageObject FixtureGroup implementation."""
from __future__ import annotations

from typing import Any


class FixtureGroup:
    """Named bundle of fixtures that can be moved or rotated together.

    Note:
        This only groups fixtures within stages but has nothing to do with FixtureGroup's from show files.

    The group's own position is the centroid of its members at creation
    time; the editor widget applies deltas to all members when the group
    is transformed.

    """

    def __init__(self, group_id: str, name: str = "",
                 position: tuple[float, float, float] | None = None,
                 rotation: tuple[float, float, float] | None = None,
                 member_ids: list[str] | None = None) -> None:
        """Initialize the group."""
        self.id = group_id
        self.name = name
        self.position = position if position is not None else (0.0, 0.0, 0.0)
        self.rotation = rotation if rotation is not None else (0.0, 0.0, 0.0)
        self.member_ids: list[str] = list(member_ids) if member_ids else []

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to nested dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "position": {"x": self.position[0], "y": self.position[1], "z": self.position[2]},
            "rotation": {"x": self.rotation[0], "y": self.rotation[1], "z": self.rotation[2]},
            "member_ids": list(self.member_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FixtureGroup:
        """Instantiate from deserialized data."""
        pos = data.get("position", {})
        rot = data.get("rotation", {})
        return cls(
            data.get("id", "group"),
            data.get("name", ""),
            (pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0)),
            (rot.get("x", 0.0), rot.get("y", 0.0), rot.get("z", 0.0)),
            data.get("member_ids", []),
        )
